# encoding: utf-8

# SPDX-FileCopyrightText: 2024 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import sys
from pathlib import Path
import importlib.util
import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

# ==============================================================================
#                                                             Command Definition
#
# Defines a Command data structure for registering QuNex coimmands.

@dataclass(frozen=True, slots=True)
class Command:
    name: str
    path: str
    description: Optional[str] = None
    type: Optional[str] = None
    args: Tuple[str, ...] = field(default_factory=tuple)
    has_var_kwargs: bool = False
    language: str = "python"
    com: Optional[Callable] = None

    origin: str = "core"         # "core" or "extension:<id>"
    priority: int = 0            # core=0, extension=100 (or use ordering)


# ------------------------------------------------------------------------------
#                                      Helper to compare command implementations

def _impl_id(cmd: Command) -> Optional[tuple[str, int]]:
    if cmd.com is None:
        return None
    try:
        return (str(Path(cmd.com.__code__.co_filename).resolve()), cmd.com.__code__.co_firstlineno)
    except Exception:
        return None


# ==============================================================================
#                                                                CommandRegistry
#
# Defines a CommandRegistry class for registering and querying commands.

def _inspect_callable(func: Callable) -> tuple[list[str], bool]:
    '''
    Inspects a callable to determine its accepted named arguments and whether it
    accepts variable keyword arguments.
    
    :param func: Description
    :type func: Callable
    :return: Description
    :rtype: tuple[list[str], bool]
    '''
    sig = inspect.signature(func)
    accepts = []
    has_var_kwargs = False

    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
            accepts.append(p.name)
        elif p.kind == p.VAR_KEYWORD:
            has_var_kwargs = True
        # VAR_POSITIONAL (*args) usually not useful for named-arg routing

    return accepts, has_var_kwargs


class CommandRegistry:
    """
    Class that maintains a registry of commands for QuNex and provides methods
    to register, query, and discover commands.
    """

    def __init__(self) -> None:
        self._commands_by_name: dict[str, Command] = {}
        self._discovered_packages: set[tuple[str, tuple[str, ...]]] = set()
        self._discovered_module_files: set[str] = set() 
        self._context: Optional[tuple[str, int, bool]] = None  # (origin, priority, allow_override)        
        self._default_context: tuple[str, int, bool] = ("core", 0, False)

    # --------------------------------------------------------------------------
    #                                            Registration of python commands   

    def register_python(
        self,
        func: Callable,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        type: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
        language: str = "python",
        origin: str = "core",
        priority: int = 0,
        allow_override: bool = False,
    ) -> Callable:
        """
        Decorator to register a Python command in the registry.
        """
        key = name or func.__name__
        mod = sys.modules.get(func.__module__)
        module_name = getattr(getattr(mod, "__spec__", None), "name", func.__module__)
        path = f"{module_name}.{key}"

        accepts, has_var_kwargs = _inspect_callable(func)

        if args is None:
            args = tuple(accepts)
        else:
            args = tuple(args)

        cmd = Command(
            name=key,
            path=path,
            description=description,
            type=type,
            args=args,
            has_var_kwargs=has_var_kwargs,
            language=language,
            com=func,
            origin=origin, 
            priority=priority
        )

        self._add(cmd, allow_override=allow_override)
        return func
    
    # --------------------------------------------------------------------------
    #                                          Registration of external commands

    def register_external(
        self,
        *,
        name: str,
        path: str,
        description: Optional[str] = None,
        type: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
        language: str,
        has_var_kwargs: bool = True,
        origin: str = "core",
        priority: int = 0,
        allow_override: bool = False,
    ) -> None:
        """
        Register an external command in the registry.
        """
        args = tuple(args or ())        

        cmd = Command(
            name=name,
            path=path,
            description=description,
            type=type,
            args=args,
            has_var_kwargs=has_var_kwargs,
            language=language,
            com=None,
            origin=origin, 
            priority=priority
        )
        self._add(cmd, allow_override=allow_override)

    # -------------------------------------------------------------------------
    #                                        Internal helper for adding commands

    def _add(self, cmd: Command, *, allow_override: bool) -> None:
        existing = self._commands_by_name.get(cmd.name)
        if existing is None:
            self._commands_by_name[cmd.name] = cmd
            return

        # Ignore alias-import duplicates of the same underlying function
        if _impl_id(existing) is not None and _impl_id(existing) == _impl_id(cmd):
            return

        if allow_override:
            # Extension wins if higher priority (or equal priority, last one wins)
            if cmd.priority >= existing.priority:
                self._commands_by_name[cmd.name] = cmd
                return

        raise ValueError(
            f"Duplicate command name '{cmd.name}'.\n"
            f"Existing: path={existing.path!r}, origin={existing.origin!r}, priority={existing.priority}\n"
            f"New:      path={cmd.path!r}, origin={cmd.origin!r}, priority={cmd.priority}"
        )

    def current_context_or_defaults(self) -> tuple[str, int, bool]:
        return self._context or self._default_context

    # def _add(self, cmd: Command) -> None:
    #     existing = self._commands_by_name.get(cmd.name)
    #     if existing is not None:
    #         # If it's the same underlying function loaded via an alias import, ignore
    #         if _same_implementation(existing, cmd):
    #             return
    #         raise ValueError(
    #             f"Duplicate command name '{cmd.name}'.\n"
    #             f"Existing: path={existing.path!r}, language={existing.language!r}\n"
    #             f"New:      path={cmd.path!r}, language={cmd.language!r}"
    #         )
    #     self._commands_by_name[cmd.name] = cmd

    # def _add(self, cmd: Command) -> None:
    #     existing = self._commands_by_name.get(cmd.name)
    #     if existing is not None:
    #         # If it’s truly the same command, ignore (idempotent)
    #         if (existing.path, existing.language) == (cmd.path, cmd.language):
    #             return
    #         raise ValueError(
    #             f"Duplicate command name '{cmd.name}'.\n"
    #             f"Existing: path={existing.path!r}, language={existing.language!r}\n"
    #             f"New:      path={cmd.path!r}, language={cmd.language!r}"
    #         )
    #     self._commands_by_name[cmd.name] = cmd

    # --------------------------------------------------------------------------
    #                                                                  Query API    

    def get(self, name: str) -> Optional[Command]:
        """
        Returns a Command by name, or None if not found.
        """
        return self._commands_by_name.get(name)

    def has(self, name: str) -> bool:
        """
        Returns True if a Command with the given name exists in the registry.
        """
        return name in self._commands_by_name

    def all(self) -> Tuple[Command, ...]:
        """
        Returns all registered Commands as a tuple.
        """
        # Stable order (by name) is often nicer for help text
        return tuple(self._commands_by_name[k] for k in sorted(self._commands_by_name.keys()))
    
    def all_commands(self) -> Tuple[str, ...]:
        """
        Returns all registered command names as a tuple.
        """
        return tuple(sorted(self._commands_by_name.keys()))
    
    def gmri_commands(self) -> Tuple[str, ...]:
        """
        Returns all matlab and python commands.
        """
        return tuple(
            sorted(
                c.name
                for c in self._commands_by_name.values()
                if c.language in ("matlab", "python")
            )
        )
        
    def iter(
        self,
        *,
        language: Optional[str] = None,
        type: Optional[str] = None,
        name_prefix: Optional[str] = None,
        path_prefix: Optional[str] = None,
        has_callable: Optional[bool] = None,
    ) -> Iterator[Command]:
        """
        Iterator over Commands, with optional filtering.
        :param language: If provided, only commands with this language are included.
        :param type: If provided, only commands of this type are included.
        :param name_prefix: If provided, only commands whose names start with this prefix are included.
        :param path_prefix: If provided, only commands whose paths start with this prefix are included.
        :param has_callable: If True, only commands with a callable are included.
                             If False, only commands without a callable are included.
                             If None, no filtering on callable presence is done.
        """
        for cmd in self.all():
            if language is not None and cmd.language != language:
                continue
            if type is not None and cmd.type != type:
                continue
            if name_prefix is not None and not cmd.name.startswith(name_prefix):
                continue
            if path_prefix is not None and not cmd.path.startswith(path_prefix):
                continue
            if has_callable is not None:
                if has_callable and cmd.com is None:
                    continue
                if (not has_callable) and cmd.com is not None:
                    continue
            yield cmd

    # --------------------------------------------------------------------------
    #                                                 Export API (derived views)

    def export_qunex_list(
        self,
        *,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[Tuple[str, Optional[str], str]]:
        """
        Reurns a list of commands: (path, description, language).
        """
        return [(c.path, c.description, c.language) for c in self.iter(language=language, type=type)]

    # --------------------------------------------------------------------------
    #                                                          Dynamic discovery

    def discover(self, package: str, *, origin: str, priority: int, allow_override: bool) -> None:
        prev = self._context
        self._context = (origin, priority, allow_override)
        
        try:
            # Resolve spec first (helps canonicalize name)
            spec = importlib.util.find_spec(package)
            if spec is None:
                raise ValueError(f"Cannot find package '{package}'")

            # Canonical import name (prevents some aliasing)
            canonical_name = spec.name
            pkg = importlib.import_module(canonical_name)

            if not hasattr(pkg, "__path__"):
                raise ValueError(f"'{canonical_name}' is not a package (no __path__)")

            # Resolve package paths to make an identity key
            pkg_paths = tuple(sorted(str(Path(p).resolve()) for p in pkg.__path__))
            pkg_key = (canonical_name, pkg_paths)

            if pkg_key in self._discovered_packages:
                return

            # Walk and import submodules, but skip modules already loaded
            for modinfo in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
                name = modinfo.name

                # If already imported under this name, skip
                if name in sys.modules:
                    continue

                mod = importlib.import_module(name)

                # Track resolved file path so even if imported again under a different name, we can detect it
                mod_file = getattr(mod, "__file__", None)
                if mod_file:
                    self._discovered_module_files.add(str(Path(mod_file).resolve()))

            self._discovered_packages.add(pkg_key)

        finally:
            self._context = prev



# ==============================================================================
#                              Module-level singleton + compatible decorator API

registry = CommandRegistry()

# ------------------------------------------------------------------------------
#                                               Module-level decorator functions

def register_command(name=None, description=None, type=None, args=None):
    """
    Decorator to register a Python command in the global registry.
    """
    def decorator(func: Callable) -> Callable:
        origin, priority, allow_override = registry.current_context_or_defaults()
        return registry.register_python(
            func,
            name=name,
            description=description,
            type=type,
            args=args,
            language="python",
            origin=origin, 
            priority=priority, 
            allow_override=allow_override
        )
    return decorator

# ------------------------------------------------------------------------------
#                                         Module-level external registration API

def register_external_command(
    *,
    name: str,
    path: str,
    language: str,
    description: Optional[str] = None,
    type: Optional[str] = None,
    args: Optional[Sequence[str]] = None,
    has_var_kwargs: bool = True,
    origin: Optional[str] = None,
    priority: Optional[int] = None,
    allow_override: Optional[bool] = None,
) -> None:
    """
    Register an external (non-python-callable) command.

    If origin/priority/allow_override are not provided, they are taken from the
    current discovery context (or defaults).
    """
    ctx_origin, ctx_priority, ctx_allow_override = registry.current_context_or_defaults()

    registry.register_external(
        name=name,
        path=path,
        description=description,
        type=type,
        args=args,  # becomes call_args
        has_var_kwargs=has_var_kwargs,
        language=language,
        origin=origin if origin is not None else ctx_origin,
        priority=priority if priority is not None else ctx_priority,
        allow_override=allow_override if allow_override is not None else ctx_allow_override,
    )