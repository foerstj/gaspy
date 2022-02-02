from matplotlib import pyplot as plt


def save_image(pic: list[list[float]], file_name):
    pic = [[pic[z][x] for z in range(len(pic[x]))] for x in range(len(pic))]  # flip x/z
    plt.imshow(pic, cmap='gray')
    plt.savefig(f'output/{file_name}.png', bbox_inches='tight')
