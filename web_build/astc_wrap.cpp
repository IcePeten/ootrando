#include <cstdint>
#include <cstddef>

#include "astcenc.h"

static int run(int encode, uint8_t* rgba, uint8_t* blocks, size_t len, int w, int h, int bw, int bh, int srgb,
               float quality) {
    astcenc_config cfg;
    astcenc_profile profile = srgb ? ASTCENC_PRF_LDR_SRGB : ASTCENC_PRF_LDR;
    unsigned flags = encode ? 0 : ASTCENC_FLG_DECOMPRESS_ONLY;
    if (astcenc_config_init(profile, bw, bh, 1, quality, flags, &cfg) != ASTCENC_SUCCESS) {
        return -1;
    }
    astcenc_context* ctx = nullptr;
    if (astcenc_context_alloc(&cfg, 1, &ctx, nullptr) != ASTCENC_SUCCESS) {
        return -2;
    }
    astcenc_image image;
    void* slices[1] = {rgba};
    image.dim_x = w;
    image.dim_y = h;
    image.dim_z = 1;
    image.data_type = ASTCENC_TYPE_U8;
    image.data = slices;
    astcenc_swizzle swizzle{ASTCENC_SWZ_R, ASTCENC_SWZ_G, ASTCENC_SWZ_B, ASTCENC_SWZ_A};
    astcenc_error status = encode ? astcenc_compress_image(ctx, &image, &swizzle, blocks, len, 0)
                                  : astcenc_decompress_image(ctx, blocks, len, &image, &swizzle, 0);
    astcenc_context_free(ctx);
    if (status == ASTCENC_SUCCESS || (!encode && status == ASTCENC_ERR_BAD_BLOCK)) {
        return 0;
    }
    return -3 - static_cast<int>(status);
}

extern "C" {

int astc_encode(uint8_t* rgba, uint8_t* blocks, size_t len, int w, int h, int bw, int bh, int srgb, float quality) {
    return run(1, rgba, blocks, len, w, h, bw, bh, srgb, quality);
}

int astc_decode(uint8_t* blocks, size_t len, uint8_t* rgba, int w, int h, int bw, int bh, int srgb) {
    return run(0, rgba, blocks, len, w, h, bw, bh, srgb, 0.0f);
}

}
