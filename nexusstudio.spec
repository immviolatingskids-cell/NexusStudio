# Build after source smoke checks: pyinstaller nexusstudio.spec
a = Analysis(['desktop.py'], pathex=['.'], datas=[('characters', 'characters'), ('reference_images', 'reference_images'), ('pools', 'pools'), ('styles', 'styles')])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name='CharacterStudio', console=False)
