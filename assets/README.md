# Shared assets

Put selected recordings, images, and model/data examples here when they should
be shared with the project. The binary formats in `.gitattributes` use Git LFS.
Keep their attribution and source/license information alongside them in text
or JSON files. SVG and other text-based files use ordinary Git.

Downloaded corpora belong in `data/`, model caches in `models/`, and experiments
in `outputs/`; those directories remain ignored. The `assets/` exception allows
deliberate binary additions without force-adding local downloads.

Before adding an asset, run `git lfs install --local`, then use normal
`git add assets/<filename>`. Check `git lfs ls-files` to see tracked binary files.
Git push uploads the LFS objects through the installed pre-push hook.
