# Avato bundled/local asset licenses

The repository does not contain user media, commercial music, or downloaded
model weights.

The three local-development music files (`calm-local`, `emotional-local`, and
`upbeat-local`) are generated from sine waves by
`backend/scripts/seed_local_assets.py`. They are original procedural test
fixtures dedicated to the public domain under CC0-1.0. They exist to exercise
the complete music-selection and mixing contract and are not intended as the
production music catalog.

Production music must be replaced with tracks for which the operator has an
explicit redistribution and synchronization license. Store the license name and
source URL in `music_tracks` and retain the agreement outside this repository.

The web UI bundles the Estedad variable font by Amin Abedi from the
[official Estedad repository](https://github.com/aminabedi68/Estedad). Estedad
is distributed under the SIL Open Font License 1.1; a copy is stored alongside
the font at `web/src/app/fonts/OFL-Estedad.txt`. FFmpeg continues to resolve
DejaVu Sans inside the backend image for rendered media.

The final transcription smoke used one temporary sample from the CC0-1.0
`hezarai/common-voice-13-fa` repackaging of Mozilla Common Voice. It was fetched
only into a temporary directory, repeated to meet the five-second input minimum, and was
not committed or redistributed with Avato. Its temporary QA account and stored
objects were deleted after verification.
