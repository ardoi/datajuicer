# -*- mode: python -*-
a = Analysis(['run_qt.py'],
             pathex=['/Users/ardoillaste/code/juicer/juicer'],
             hiddenimports=['scipy.special._ufuncs_cxx'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Juicer',
          debug=False,
          strip=None,
          upx=True,
          console=True )
bftools = Tree('lib/bftools',prefix='bftools')
coll = COLLECT(exe,
               a.binaries,
               bftools,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='resources')
