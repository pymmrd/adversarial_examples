"""
FGSM tutorial on cifar10 using advbox tool.
FGSM method is non-targeted attack while FGSMT is targeted attack.
"""
import sys
sys.path.append("..")

import matplotlib.pyplot as plt
import numpy as np
import paddle.fluid as fluid
import paddle.v2 as paddle

from advbox.adversary import Adversary
#from advbox.attacks.gradient_method import FGSM
#from advbox.attacks.gradient_method import FGSMT
from advbox.attacks.deepfool import DeepFoolAttack
from advbox.models.paddle import PaddleModel
#from tutorials.mnist_model import mnist_cnn_model
#from vgg import vgg_bn_drop
from resnet import resnet_cifar10

def main():
    """
    Advbox demo which demonstrate how to use advbox.
    """
    TOTAL_NUM = 500
    IMG_NAME = 'img'
    LABEL_NAME = 'label'

    img = fluid.layers.data(name=IMG_NAME, shape=[3, 32, 32], dtype='float32')
    # gradient should flow
    img.stop_gradient = False
    label = fluid.layers.data(name=LABEL_NAME, shape=[1], dtype='int64')
    
    #logits = mnist_cnn_model(img)
    #logits = vgg_bn_drop(img)
    logits = resnet_cifar10(img,32)
    
    cost = fluid.layers.cross_entropy(input=logits, label=label)
    avg_cost = fluid.layers.mean(x=cost)

    # use CPU
    #place = fluid.CPUPlace()
    # use GPU
    place = fluid.CUDAPlace(0)
    exe = fluid.Executor(place)

    BATCH_SIZE = 1
    test_reader = paddle.batch(
        paddle.dataset.cifar.test10(), batch_size=BATCH_SIZE)

    fluid.io.load_params(
        exe, "cifar10/", main_program=fluid.default_main_program())

    # advbox demo
    m = PaddleModel(
        fluid.default_main_program(),
        IMG_NAME,
        LABEL_NAME,
        logits.name,
        avg_cost.name, (-1, 1),
        channel_axis=1)
    #attack = FGSM(m)
    attack = DeepFoolAttack(m)
    # attack = FGSMT(m)
    #attack_config = {"epsilons": 0.3}
    attack_config = {"iterations": 100, "overshoot": 9}
    # use test data to generate adversarial examples
    total_count = 0
    fooling_count = 0
    for data in test_reader():
        total_count += 1
        adversary = Adversary(data[0][0], data[0][1])

        # FGSM non-targeted attack
        adversary = attack(adversary, **attack_config)

        # FGSMT targeted attack
        # tlabel = 0
        # adversary.set_target(is_targeted_attack=True, target_label=tlabel)
        # adversary = attack(adversary, **attack_config)

        if adversary.is_successful():
            fooling_count += 1
            print(
                'attack success, original_label=%d, adversarial_label=%d, count=%d'
                % (data[0][1], adversary.adversarial_label, total_count))
            # plt.imshow(adversary.target, cmap='Greys_r')
            # plt.show()
            # np.save('adv_img', adversary.target)
        else:
            print('attack failed, original_label=%d, count=%d' %
                  (data[0][1], total_count))

        if total_count >= TOTAL_NUM:
            print(
                "[TEST_DATASET]: fooling_count=%d, total_count=%d, fooling_rate=%f"
                % (fooling_count, total_count,
                   float(fooling_count) / total_count))
            break
    #print("fgsm attack done")
    print("deelfool attack done")

if __name__ == '__main__':
    main()
