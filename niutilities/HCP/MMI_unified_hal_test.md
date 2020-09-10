```bash
qx hcp_PreFS \
  --sessionsfolder="/Volumes/tigr/MBLab/fMRI/MMI/subjects.j" \
  --sessions="/Volumes/tigr/MBLab/fMRI/MMI/processing/batch_unified.txt" \
  --overwrite="yes"
```

```bash
qx hcp_FS \
  --sessionsfolder="/Volumes/tigr/MBLab/fMRI/MMI/subjects.j" \
  --sessions="/Volumes/tigr/MBLab/fMRI/MMI/processing/batch_unified.txt" \
  --overwrite="yes"
```

```bash
qx hcp_fMRIVolume \
  --sessionsfolder="/Volumes/tigr/MBLab/fMRI/MMI/subjects.j" \
  --sessions="/Volumes/tigr/MBLab/fMRI/MMI/processing/batch_unified.txt" \
  --overwrite="yes"
```

```bash
rsync -avzHn --include="/ZK4M8/T1w/***" --include="/ZK4M8/T2w/***" --include="/ZK4M8/MNINonLinear/***" --include="/ZK4M8/unprocessed/***" --exclude="*" /gpfs/project/fas/n3/Studies/MBLab/MMI/subjects/ZK4M8/hcp/ hal:/Volumes/tigr/MBLab/fMRI/MMI/subjects.j/ZK4M8/hcp

rsync -avzH --include="/ZK4M8" --include="hcp/" --include="ZK4M8/" --include="T*/***" --include="MNI*/***" --include="un*/***" --exclude="*" /gpfs/project/fas/n3/Studies/MBLab/MMI/subjects/ hal:/Volumes/tigr/MBLab/fMRI/MMI/subjects.j

rsync -avzHn --include="unprocessed/***" --include="T1w/***" --include="T2w/***" --include="MNINonLinear/***" /gpfs/project/fas/n3/Studies/MBLab/MMI/subjects/ZK4M8/hcp/ZK4M8/ hal:/Volumes/tigr/MBLab/fMRI/MMI/subjects.j/ZK4M8
```

/gpfs/project/fas/n3/Studies/MBLab/MMI/subjects/ZK4M8/hcp/ZK4M8/