# encoding: utf-8

# SPDX-FileCopyrightText: 2024 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later


from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
try:
    from qx_utilities.general import exceptions as ge
except ModuleNotFoundError:
    from general import exceptions as ge


DEFAULT_CORE_REGISTRY_BASENAME = "qx_commands.yaml"
DEFAULT_EXTENSION_REGISTRY_FILENAME = "qx_commands.yaml"


@dataclass(frozen=True)
class ArgInfo:
    name: str
    type: Optional[str] = None
    default: Optional[str] = None
    description: Optional[str] = None  # short: up to first empty line


@dataclass(frozen=True)
class CommandInfo:
    name: str
    aliases: Tuple[str, ...]
    path: str
    language: str
    call: Optional[str]
    description: Optional[str]
    type: Optional[str]
    args: Tuple[ArgInfo, ...]        # ordered by function signature
    options: Tuple[ArgInfo, ...]     # populated only if signature has 'options'
    returns: Tuple[ArgInfo, ...]     # ordered as listed in Returns:
    origin: str
    # optional `logging:` from the qx_command block: none|comlog|runlog|both.
    # None means the command states nothing and the settings files decide.
    logging: Optional[str] = None


@dataclass(frozen=True)
class Registry:
    version: int
    generated_at: str
    source_id: str
    commands: Tuple[CommandInfo, ...]


class Command:
    """Runtime wrapper: exposes CommandInfo fields + lazy loading helpers."""
    __slots__ = ("info", "_registry")

    def __init__(self, info: CommandInfo, registry: "CommandRegistry") -> None:
        self.info = info
        self._registry = registry

    def __getattr__(self, name: str) -> Any:
        # Delegate attribute access to the underlying CommandInfo
        return getattr(self.info, name)

    def load_callable(self) -> Callable:
        return self._registry.load_callable(self.info)

    def has_arg(self, name: str) -> bool:
        return any(arg.name == name for arg in self.args)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def registry_from_obj(obj: Dict[str, Any]) -> Registry:
    cmds: List[CommandInfo] = []
    source_id = (obj.get("source") or {}).get("id", "unknown")
    generated_at = obj.get("generated_at") or ""
    version = int(obj.get("version") or 1)

    def load_args(lst: list[dict[str, Any]]) -> Tuple[ArgInfo, ...]:
        return tuple(
            ArgInfo(
                name=a.get("name"),
                type=a.get("type"),
                default=a.get("default"),
                description=a.get("description"),
            )
            for a in (lst or [])
        )

    for c in obj.get("commands", []):
        cmds.append(
            CommandInfo(
                name=c["name"],
                aliases=tuple(c.get("aliases") or ()),
                path=c["path"],
                language=c.get("language", "python"),
                call=c.get("call"),
                description=c.get("description"),
                type=c.get("type"),
                args=load_args(c.get("args") or []),
                options=load_args(c.get("options") or []),
                returns=load_args(c.get("returns") or []),
                origin=c.get("origin", source_id),
                logging=c.get("logging"),
            )
        )

    return Registry(version=version, generated_at=generated_at, source_id=source_id, commands=tuple(cmds))


def read_registry_file(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    data = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        return json.loads(data)

    # only the import falls back to JSON; a YAML syntax error must surface as a
    # YAML error rather than a confusing JSON one.
    # CSafeLoader (libyaml) is ~10x faster and this is parsed on every gmri call.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(data, Loader=loader)


def load_registry_yaml(path: str | Path) -> Registry:
    return registry_from_obj(read_registry_file(Path(path)))


def merge_registries(
    base: Registry,
    overlays: List[Registry],
) -> Tuple[Registry, Dict[str, CommandInfo]]:
    # override by command name
    by_name: Dict[str, CommandInfo] = {c.name: c for c in base.commands}
    for reg in overlays:
        for c in reg.commands:
            by_name[c.name] = c

    merged_cmds = list(by_name.values())

    # token map (names + aliases must be globally unique)
    token_map: Dict[str, CommandInfo] = {}
    for c in merged_cmds:
        for t in (c.name,) + c.aliases:
            if t in token_map:
                prev = token_map[t]
                raise ge.CommandFailed('merge_registries',
                    f"After merge, token '{t}' is ambiguous.\n"
                    f"Used by: {prev.name} ({prev.origin})\n"
                    f"Also by: {c.name} ({c.origin})"
                )
            token_map[t] = c

    merged = Registry(
        version=max([base.version] + [r.version for r in overlays] or [1]),
        generated_at=_now_utc_iso(),
        source_id=base.source_id,
        commands=tuple(sorted(merged_cmds, key=lambda x: x.name)),
    )
    return merged, token_map


def load_python_callable(command: CommandInfo):
    if command.language != "python":
        raise ge.CommandFailed('load_python_callable', f"Not a python command: {command.language}")

    mod_path, _, fn_name = command.path.rpartition(".")
    if not mod_path:
        raise ge.CommandFailed('load_python_callable', f"Invalid python command.path: {command.path}")
    import importlib
    mod = importlib.import_module(mod_path)
    return getattr(mod, fn_name)


def _split_env_path_list(value: str) -> List[str]:
    value = (value or "").strip()
    if not value:
        return []
    value = value.replace(";", ":")
    return [p.strip() for p in value.split(":") if p.strip()]


def extension_search_roots() -> List[Path]:
    roots: List[Path] = []

    qunexpath = os.environ.get("QUNEXPATH", "").strip()
    if qunexpath:
        roots.append(Path(qunexpath) / "qx_extensions")

    tools = os.environ.get("TOOLS", "").strip()
    if tools:
        roots.append(Path(tools) / "qx_extensions")

    extra = os.environ.get("QUNEXEXTENSIONFOLDERS", "").strip()
    for folder in _split_env_path_list(extra):
        roots.append(Path(folder))

    # de-dup preserving order
    seen = set()
    uniq: List[Path] = []
    for r in roots:
        rr = r.expanduser()
        try:
            rr = rr.resolve()
        except Exception:
            pass
        s = str(rr)
        if s not in seen:
            seen.add(s)
            uniq.append(rr)
    return uniq


def discover_extension_registries(
    *,
    registry_filename: str = DEFAULT_EXTENSION_REGISTRY_FILENAME,
    require_registry_file: bool = True,
) -> List[Tuple[str, Path]]:
    """
    Find extension registries at:
      <root>/qx_<name>/<registry_filename>

    Returns: [("extension:<name>", Path(.../qx_<name>/qx_commands.yaml)), ...]

    If the same extension exists in multiple roots, later roots override earlier ones.
    """
    roots = extension_search_roots()
    found: Dict[str, Path] = {}

    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for ext_dir in sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("qx_")]):
            ext_name = ext_dir.name[len("qx_") :].strip()
            if not ext_name:
                continue
            reg_path = ext_dir / registry_filename
            if require_registry_file and not reg_path.exists():
                continue
            found[f"extension:{ext_name}"] = reg_path

    return sorted(found.items(), key=lambda x: x[0])


def load_qx_registry(
    *,
    core_registry_path: Optional[str | Path] = None,
    extension_registry_filename: str = DEFAULT_EXTENSION_REGISTRY_FILENAME,
    require_extension_registry: bool = True,
) -> Tuple[Registry, Dict[str, CommandInfo]]:
    """
    Load core from $QUNEXPATH/qx_commands.yaml, then discover & merge extension registries.
    """
    if core_registry_path is None:
        qunexpath = os.environ.get("QUNEXPATH", "").strip()
        if not qunexpath:
            raise ge.CommandError('load_qx_registry', "QUNEXPATH is not set and no core_registry_path was provided.")
        core_registry_path = Path(qunexpath) / DEFAULT_CORE_REGISTRY_BASENAME

    core_registry_path = Path(core_registry_path).resolve()
    if not core_registry_path.exists():
        raise ge.CommandError('load_qx_registry', f"Core registry not found: {core_registry_path}")

    core = load_registry_yaml(core_registry_path)

    exts = discover_extension_registries(
        registry_filename=extension_registry_filename,
        require_registry_file=require_extension_registry,
    )
    overlay_regs = [load_registry_yaml(p) for _id, p in exts]

    return merge_registries(core, overlay_regs)


CommandRef = Union[str, CommandInfo, Command]


class CommandRegistry:
    """
    Queryable registry wrapper around a merged Registry + token_map.

    Note:
      - No `com` stored. Use `load_callable()` for python commands.
      - token_map maps command name OR alias -> CommandInfo (input)
    """

    def __init__(
        self,
        registry: Registry,
        token_map: Dict[str, CommandInfo],
        *,
        core_registry_path: Optional[Path] = None,
        extension_registry_filename: str = DEFAULT_EXTENSION_REGISTRY_FILENAME,
        require_extension_registry: bool = True,
    ) -> None:
        self._registry = registry

        # for reload()
        self._core_registry_path = core_registry_path
        self._extension_registry_filename = extension_registry_filename
        self._require_extension_registry = require_extension_registry

        # cache for python callables: path -> callable
        self._callable_cache: Dict[str, Callable] = {}

        # ---- NEW: build runtime Command wrappers

        # Unique Command wrappers by canonical name
        self._commands_by_name: Dict[str, Command] = {
            info.name: Command(info, self) for info in registry.commands
        }

        # Token map: name + aliases -> Command wrapper
        self._commands_by_token: Dict[str, Command] = {}
        for token, info in token_map.items():
            cmd = self._commands_by_name.get(info.name)
            if cmd is None:
                # Should not happen unless registry/token_map are inconsistent
                continue
            self._commands_by_token[token] = cmd

    # -------------------------
    # basic container behavior
    # -------------------------

    def __len__(self) -> int:
        return len(self._registry.commands)

    def __contains__(self, name_or_alias: str) -> bool:
        return name_or_alias in self._commands_by_token

    @property
    def registry(self) -> Registry:
        return self._registry

    # -------------------------
    # lookups
    # -------------------------

    def get(self, name_or_alias: str, default: Optional[Command] = None) -> Optional[Command]:
        return self._commands_by_token.get(name_or_alias, default)

    def require(self, name_or_alias: str) -> Command:
        cmd = self.get(name_or_alias)
        if cmd is None:
            raise ge.CommandFailed('CommandRegistry.require', f"Unknown command: {name_or_alias}")
        return cmd

    # -------------------------
    # iteration & filtering
    # -------------------------

    def iter(self, *, language: Optional[str] = None, origin: Optional[str] = None, type: Optional[str] = None):
        for cmd in self._commands_by_name.values():
            info = cmd.info
            if language is not None and info.language != language:
                continue
            if origin is not None and info.origin != origin:
                continue
            if type is not None and info.type != type:
                continue
            yield cmd

    # -------------------------
    # export helpers
    # -------------------------

    def gmri_commands(self) -> List[str]:
        """
        The commands `gmri` runs, which is every command it knows of but one.

        `bin/qunex.sh` hands over everything this reports and handles the rest
        itself, so this function is the routing: the wrappers for the bash
        commands are still in that file and are simply no longer reached.
        `run_turnkey` is the exception, and keeps its old path until it is
        retired.
        """
        return [c.name for c in self.iter() if c.name not in ("run_turnkey",)]

    def to_qunex_list(self) -> List[Tuple[str, str, Optional[str], str]]:
        """
        List of (name, path, description, language) for every command.

        Note: path is:
          - python: dotted module.func
          - matlab: relative .m path
          - r: TBD
        """
        return [(c.name, c.path, c.description, c.language) for c in self.iter()]

    # -------------------------
    # python callable resolution
    # -------------------------

    def load_callable(self, cmd: CommandRef) -> Callable:
        """
        For python commands only: lazily import and return the function.

        Accepts:
        - command name/alias (str)
        - Command (wrapper)
        - CommandInfo
        """
        if isinstance(cmd, str):
            info = self.require(cmd).info          # require() returns Command
        elif isinstance(cmd, Command):
            info = cmd.info
        else:
            info = cmd                              # CommandInfo

        if info.language != "python":
            raise ge.CommandFailed('CommandRegistry.load_callable', "command not python",
                f"Cannot load callable for non-python command: {info.name} (language={info.language})"
            )

        cached = self._callable_cache.get(info.path)
        if cached is not None:
            return cached

        fn = load_python_callable(info)            # expects CommandInfo
        self._callable_cache[info.path] = fn
        return fn

    # -------------------------
    # reload support
    # -------------------------

    def reload(self) -> None:
        reg, token_map = load_qx_registry(
            core_registry_path=self._core_registry_path,
            extension_registry_filename=self._extension_registry_filename,
            require_extension_registry=self._require_extension_registry,
        )
        self._registry = reg
        self._callable_cache.clear()

        # rebuild wrappers
        self._commands_by_name = {info.name: Command(info, self) for info in reg.commands}
        self._commands_by_token = {}

        for token, info in token_map.items():
            cmd = self._commands_by_name.get(info.name)
            if cmd is not None:
                self._commands_by_token[token] = cmd


def load_command_registry(
    *,
    core_registry_path: Optional[str | Path] = None,
    extension_registry_filename: str = DEFAULT_EXTENSION_REGISTRY_FILENAME,
    require_extension_registry: bool = True,
) -> CommandRegistry:
    reg, token_map = load_qx_registry(
        core_registry_path=core_registry_path,
        extension_registry_filename=extension_registry_filename,
        require_extension_registry=require_extension_registry,
    )
    return CommandRegistry(
        reg,
        token_map,
        core_registry_path=Path(core_registry_path).resolve() if core_registry_path is not None else None,
        extension_registry_filename=extension_registry_filename,
        require_extension_registry=require_extension_registry,
    )


_registry: Optional[CommandRegistry] = None


class _RegistryProxy:
    def _real(self) -> CommandRegistry:
        global _registry
        if _registry is None:
            _registry = load_command_registry()
        return _registry

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real(), name)

    def reload(self) -> None:
        global _registry
        if _registry is None:
            _registry = load_command_registry()
        else:
            _registry.reload()


qx_commands = _RegistryProxy()
