from perlin_noise import PerlinNoise


def make_perlin(seed, max_size_xz, octaves_per_km):
    waves_per_km = 2**octaves_per_km
    waves = max_size_xz * 4 / 1000 * waves_per_km
    perlin = PerlinNoise(waves, seed)
    return perlin
