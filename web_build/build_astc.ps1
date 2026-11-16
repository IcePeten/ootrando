Set-Location $PSScriptRoot
& "$env:USERPROFILE\emsdk\emsdk_env.ps1" *> $null
$src = Get-ChildItem "$env:USERPROFILE\astc-encoder\Source\astcenc_*.cpp" | ForEach-Object { $_.FullName }
$flags = @('-O3', '-std=c++20', '-DASTCENC_SSE=0', '-DASTCENC_AVX=0', '-DASTCENC_NEON=0', '-DASTCENC_SVE=0',
    '-DASTCENC_POPCNT=0', '-DASTCENC_F16C=0', '-I', "$env:USERPROFILE\astc-encoder\Source", 'astc_wrap.cpp') + $src + @(
    '-o', 'astcenc.js', '-sMODULARIZE=1', '-sEXPORT_NAME=AstcModule', '-sSINGLE_FILE=1', '-sALLOW_MEMORY_GROWTH=1',
    '-sENVIRONMENT=web,worker,node', '-sEXPORTED_FUNCTIONS=_astc_encode,_astc_decode,_malloc,_free',
    '-sEXPORTED_RUNTIME_METHODS=HEAPU8')
& em++ @flags
