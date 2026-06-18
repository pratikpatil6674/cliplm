# Nuitka

uv run python -m nuitka     --standalone     --onefile     --plugin-enable=pyside6     --remove-output     --disable-console     --nofollow-import-to=unittest,tkinter,test     src/main.py

# Snap

snap pack
sudo snap install --dangerous cliplm_0.1.0_amd64.snap
snapcraft upload --release=edge cliplm_1.0_amd64.snap
channels: edge, beta, candidate, stable.
snapcraft status cliplm
snapcraft register cliplm

