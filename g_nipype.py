import os
from nipype.interfaces.base import BaseInterface, InputMultiPath,\
    OutputMultiPath, BaseInterfaceInputSpec, traits, File, Directory, TraitedSpec
from nipype.interfaces.utility import Function, FunctionInputSpec
from nipype.pipeline.engine import Node, MapNode, Workflow
from nipype.interfaces.io import DataGrabber, DataSink
import nipype.interfaces.utility as util
from os import getcwd, getenv

# the workflow subclass
class G_Step0Workflow(Workflow):
    input_node = None
    subjects_node = None
    dicom_grabber = None
    dicom_sorter = None
    dicom_converter = None
    def __init__(self, *args, **kwargs):
        super(G_Step0Workflow, self).__init__(*args, **kwargs)
        self.initNodes();

    def initNodes(self):
        # a node for common inputs
        # input node 
        self.input_node = Node(
                name='input_node',
                interface=util.IdentityInterface(fields=['subj_dir_template','base_dir']))
        # split pipeline by sub_num
        self.subjects_node = Node(
                name='iter_subs',
                interface=util.IdentityInterface(
                    fields=['sub_num']))
        # self.subjects_node.iterables = ('sub_num', [6])      <-- you'll want to set this!
        # a node to derive the subject dir template...
        self.derive_sub_dir = Node(
                name='derive_subject_dir',
                interface=util.Function(
                        input_names=['sub_dir_template', 'sub_num'],
                        output_names=['sub_dir'],
                        function=derive_sub_dir))
        """
        DICOM_GRABBER CONFIG
        --------------------
        self.dicom_grabber.inputs.field_template
            required. set to full path glob, or partial path glob after base_directory. eg:
            {'dicom': 'S%03d/scans/*/resources/DICOM/files/*.dcm'}
        self.dicom_grabber.inputs.template_args
            optional, but default just passes sub_num to the template once. eg:
            {'dicom': [['sub_num']]}
        """
        self.dicom_grabber = Node(
                name='dicom_data_source',
                interface=DataGrabber(
                        infields=['sub_num'],
                        outfields=['dicom'],))
        self.dicom_grabber.inputs.sort_filelist = False
        self.dicom_grabber.inputs.template = '*'
        self.dicom_grabber.inputs.template_args = {'dicom':[['sub_num']]}
        self.dicom_grabber.inputs.base_directory = getcwd()
        # dicom sorting node
        self.dicom_sorter = Node(name='dicom_sorter', interface=G_SortInterface())
        # dicom converting node
        self.dicom_converter = Node(name='dicom_converter', interface=G_DicomConvert())
        # connect the nodes
        self.connect([
                (self.input_node, self.dicom_grabber,
                        [('base_dir','base_directory')]),
                (self.input_node, self.derive_sub_dir,
                        [('subj_dir_template','sub_dir_template')]),
                (self.subjects_node, self.derive_sub_dir,
                        [('sub_num','sub_num')]),
                (self.subjects_node, self.dicom_grabber,
                        [('sub_num','sub_num')]),
                (self.derive_sub_dir, self.dicom_grabber,
                        [('sub_dir','out_dir')]),
                (self.dicom_grabber, self.dicom_sorter,
                        [('dicom', 'dicom_files')]),
                (self.derive_sub_dir, self.dicom_sorter,
                        [('sub_dir', 'out_dir')]),
                (self.dicom_sorter, self.dicom_converter,
                        [('out_dir','subj_directory')]),
                ])

class G_SortInterfaceInputSpec(BaseInterfaceInputSpec):
    dicom_files = InputMultiPath(
            traits.Either(traits.List(File(exists=True)),File(exists=True)),
            mandatory=True,
            desc='list of dicom files to sort',
            copyfile=False)
    out_dir = Directory(
            value='.',
            usedefault=True,
            mandatory=False,
            exists=True,
            desc='directory to use for output. a "dicom" subdir will be created here.')
    copy_files = traits.Bool(True,
            usedefault=True,
            mandatory=False,
            desc='determines whether files are moved or copied. default is to copy.')

class G_SortInterfaceOutputSpec(TraitedSpec):
    dicom_files = OutputMultiPath(traits.List(File(exists=True)),
            desc='full paths of the relocated dicom files')
    out_dir = Directory(
            value='.',
            exists=True,
            desc='directory used for output. will contain "dicom" dir')

class G_SortInterface(BaseInterface):
    input_spec = G_SortInterfaceInputSpec
    output_spec = G_SortInterfaceOutputSpec

    def _run_interface(self, runtime):
        from g_mri.g_dicom import sortDicom
        d_files = self.inputs.dicom_files
        out_dir = self.inputs.out_dir
        print "the out dir is %s" % out_dir
        copy_files = self.inputs.copy_files
        sortDicom(files=d_files, out_dir=out_dir, copy=copy_files)
        return runtime

    def _list_outputs(self):
        from glob import glob
        import os
        outputs = self._outputs().get()
        out_glob = os.path.join(self.inputs.out_dir, 'dicom', '*', '*.dcm*')
        outputs['dicom_files'] = glob(out_glob)
        outputs['out_dir'] = self.inputs.out_dir
        return outputs

class G_DicomConvertInputSpec(BaseInterfaceInputSpec):
    subj_directory = Directory(
            value='.',
            usedefault=True,
            mandatory=False,
            exists=True,
            desc='the subject directory')

class G_DicomConvertOutputSpec(TraitedSpec):
    nii_files = OutputMultiPath(traits.List(File(exists=True)),
            desc='full paths of the relocated dicom files')

class G_DicomConvert(BaseInterface):
    input_spec = G_DicomConvertInputSpec
    output_spec = G_DicomConvertOutputSpec
    def _run_interface(self, runtime):
        from g_mri.g_dicom import dicom2nii
        s_dir = self.inputs.subj_directory
        dicom2nii(folder=s_dir, clean='yes', unzip='yes', gzip='yes')
        return runtime

    def _list_outputs(self):
        from glob import glob
        import os
        outputs = self._outputs().get()
        out_glob = os.path.join(self.inputs.subj_directory, 'nii', '*.nii*')
        outputs['nii_files'] = glob(out_glob)
        return outputs

def derive_sub_dir(sub_dir_template, sub_num):
    return sub_dir_template % sub_num


