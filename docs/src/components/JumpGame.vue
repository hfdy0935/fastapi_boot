<template>
    <div class="outer">
        <!-- 复活对话框 -->
        <Modal v-model:open="isFailTipShow" title="游戏结束" :onCancel="failEvent">
            <template #footer>
                <Button type="primary" @click="reCharge">充值6块复活</Button>
            </template>
        </Modal>
        <!-- 容器 -->
        <div
            ref="container"
            class="jump-container"
            @mousedown="handleMousedown"
            @mouseup="handleMouseup"
            @touchstart="handleMousedown"
            @touchend="handleMouseup"></div>
        <!-- 显示当前信息 -->
        <Card
            class="card"
            :bodyStyle="{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 0
            }">
            <!-- <Button type="primary" @mousedown="handleMousedown" @mouseup="handleMouseup" @touchstart="handleMousedown"
                @touchend="handleMouseup" :disabled="isJumping">跳</Button> -->
            <span>距离： {{ range }}</span>
            <span>分数： {{ score }}</span>
            动感<Switch v-model:checked="isCameraYChange"></Switch>
            <Button type="primary" @click="saveAsImage">存图</Button>
            <Button type="primary" danger @click="restart" :disabled="isJumping">重置</Button>
        </Card>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { storeToRefs } from 'pinia';
import { useJumpGameStore, type aBoxAttrType } from '/src/stores';
import * as THREE from 'three';
import { message, Button, Card, Modal, Switch } from 'ant-design-vue';
import 'ant-design-vue/lib/button/style';
defineOptions({ name: 'JumpGame' });

const container = ref<HTMLDivElement>();
const { playerPosition, score, boxAttrArr, isCameraYChange } = storeToRefs(useJumpGameStore());
const { createNextBox, addBoxAttrToArr, shiftBoxAttrArr, reset } = useJumpGameStore();
const scene: THREE.Scene = new THREE.Scene();
scene.background = new THREE.Color('rgb(230, 178, 178)');
scene.receiveShadow = true;
const camera: THREE.PerspectiveCamera = new THREE.PerspectiveCamera(75, 1.0, 0.1, 10000);
const renderer: THREE.WebGLRenderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: true
});
renderer.shadowMap.enabled = true;
let minWidthOrHeight = ref<number>(Math.min(window.innerWidth, window.innerHeight - 100) - 80);
renderer.setSize(minWidthOrHeight.value, minWidthOrHeight.value);
renderer.setPixelRatio(Math.max(window.devicePixelRatio, 2));

// 初始化
let playerMesh: THREE.Mesh;
let pointLight: THREE.PointLight;
const initAdd = () => {
    camera.position.set(playerPosition.value[0] - 300, 500, playerPosition.value[2] + 200);
    boxAttrArr.value.forEach((item: aBoxAttrType) => {
        if (item) {
            const geometry = new THREE.BoxGeometry(...item.geometry);
            const material = new THREE.MeshPhysicalMaterial({ color: item.color });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            mesh.position.set(...item.position);
            mesh.name = 'pathBox';
            scene.add(mesh);
        }
    });

    // 主角
    const playerGeometry = new THREE.BoxGeometry(20, 50, 20);
    const playerMaterial = new THREE.MeshBasicMaterial({ color: 'red' });
    playerMesh = new THREE.Mesh(playerGeometry, playerMaterial);
    playerMesh.position.set(...playerPosition.value);
    playerMesh.name = 'player';
    playerMesh.castShadow = true;
    scene.add(playerMesh);
    const [x, y, z] = Object.values(playerMesh.position) as [number, number, number];
    camera.lookAt(x + 300, y, z - 300);

    // 灯光
    pointLight = new THREE.PointLight(0xffffff, 500000);
    pointLight.position.set(playerPosition.value[0] - 300, 300, playerPosition.value[2] + 200);
    pointLight.castShadow = true;
    scene.add(pointLight);
};
initAdd();

// 移除scene中第一个mesh
const removeFirstMeshFromScene = () => {
    const box = scene.children.filter((item: any) => item.name === 'pathBox');
    if (box.length < 5) {
        return;
    }
    scene.remove(box[0]);
};

// 蓄力程度
const range = ref<number>(0);
const isIncreasingRange = ref<boolean>(false);
const handleMousedown = () => {
    isIncreasingRange.value = true;
};
const handleMouseup = () => {
    isIncreasingRange.value = false;
    playerMesh.position.y = 50;
    handleJump();
};
// 判断是否能跳到目标上
const isInTarget = (target: aBoxAttrType, message: string) => {
    if (
        playerPosition.value[0] <= target.position[0] + target.geometry[0] / 2 &&
        playerPosition.value[0] >= target.position[0] - target.geometry[0] / 2 &&
        playerPosition.value[2] <= target.position[2] + target.geometry[2] / 2 &&
        playerPosition.value[2] >= target.position[2] - target.geometry[2] / 2
    ) {
        // console.log(message);
        // console.log(
        //     `x需要满足： ${target.position[0] - target.geometry[0] / 2} <= ${playerPosition.value[0]} <= ${target.position[0] + target.geometry[0] / 2}`
        // );
        // console.log(
        //     `z需要满足：${target.position[2] - target.geometry[2] / 2} <= ${playerPosition.value[2]} <= ${target.position[2] + target.geometry[2] / 2}`
        // );
        // console.log('------------------------------------------------------------------------------------------------');
        return true;
    }
    return false;
};
const canJumpToTarget = () => {
    // next、current是下一个和目前的方块属性数组
    const next = boxAttrArr.value[3];
    const current = boxAttrArr.value[2];
    const nextNext = boxAttrArr.value[4];
    if (isInTarget(current, '情况1：还在原方块')) {
        // 还在原方块
        return 1;
    } else if (isInTarget(next, '情况2：跳到下一个方块')) {
        // 跳到下一个方块
        return 2;
    } else if (isInTarget(nextNext, '情况2.5：跳到下下个方块')) {
        // 跳到下下个方块
        return 3;
    } else {
        // console.log('情况3：失败');
        // console.log(
        //     `x需要满足： ${current.position[0] - current.geometry[0] / 2} <= ${playerPosition.value[0]} <= ${current.position[0] + current.geometry[0] / 2} 或 ${next.position[0] - next.geometry[0] / 2} <= ${playerPosition.value[0]} <= ${next.position[0] + next.geometry[0] / 2}`
        // );
        // console.log(
        //     `z需要满足： ${current.position[2] - current.geometry[2] / 2} <= ${playerPosition.value[2]} <= ${current.position[2] + current.geometry[2] / 2} 或 ${next.position[2] - next.geometry[2] / 2} <= ${playerPosition.value[2]} <= ${next.position[2] + next.geometry[2] / 2}`
        // );
        return 0;
    }
};
// 跳
const isJumping: any = ref(null);
// 游戏失败的提示是否显示
const isFailTipShow = ref<boolean>(false);
// 跳到下一格方块或者失败了点击充值复活后生成新的方块
const successJump = () => {
    const newBox = createNextBox();
    newBox.name = 'pathBox';
    removeFirstMeshFromScene();
    scene.add(newBox);
    score.value++;
    addBoxAttrToArr(newBox);
    shiftBoxAttrArr();
};
// 跳的函数
const handleJump = () => {
    // 节流
    if (isJumping.value) {
        return;
    }
    isJumping.value = true;
    // 距离
    const deltaX = boxAttrArr.value[3].position[0] - boxAttrArr.value[2].position[0] ? range.value : 0;
    const deltaZ = boxAttrArr.value[3].position[2] - boxAttrArr.value[2].position[2] ? -range.value : 0;
    // 2：还在原来的方块上，1：跳到下一个了，0：失败了
    playerMove(deltaX, deltaZ, playerMesh, camera).then(() => {
        const canReach: number = canJumpToTarget();
        if (canReach === 2) {
            successJump();
        } else if (canReach === 3) {
            message.warning('非会员禁止跳两跳');
            isFailTipShow.value = true;
        } else if (canReach === 0) {
            isFailTipShow.value = true;
        }
        range.value = 0;
        isJumping.value = false;
    });
};

// 根据前后两次的位置生成样条曲线
const generateCatmullRomCurve3 = (deltaX: number, deltaZ: number, totalStep: number) => {
    const h = totalStep;
    const x1 = playerMesh.position.x;
    const x2 = boxAttrArr.value[3].position[0];
    const z1 = playerMesh.position.z;
    const z2 = boxAttrArr.value[3].position[2];
    // 生成样条曲线
    let arr;
    if (deltaX > 0) {
        if (z1 === z2) {
            needMoveX.value = deltaX;
            needMoveZ.value = 0;
            arr = [
                new THREE.Vector3(x1, playerMesh.position.y, z1),
                new THREE.Vector3((x1 + deltaX) / 2, playerMesh.position.y + h, z1),
                new THREE.Vector3(x1 + deltaX, playerMesh.position.y, z1)
            ];
        } else {
            const z3 = (z2 - z1) / (Math.sqrt((z2 - z1) ** 2 + (x2 - x1) ** 2) / deltaX) + z1;
            const x3 = (x2 - x1) / (Math.sqrt((z2 - z1) ** 2 + (x2 - x1) ** 2) / deltaX) + x1;
            needMoveX.value = x3 - x1;
            needMoveZ.value = z3 - z1;
            // Math.sqrt((z2-z1)**2+(x2-x1)**2)/deltaX = (z2-z1)/(z3-z1) => z3
            // Math.sqrt((z2-z1)**2+(x2-x1)**2)/deltaX = (x2-x1)/(x3-x1) => x3

            arr = [
                new THREE.Vector3(x1, playerMesh.position.y, z1),
                new THREE.Vector3((x1 + x3) / 2, playerMesh.position.y + h, (z1 + z3) / 2),
                new THREE.Vector3(x3, playerMesh.position.y, z3)
            ];
        }
    } else {
        if (x1 === x2) {
            needMoveX.value = 0;
            needMoveZ.value = deltaZ;
            arr = [
                new THREE.Vector3(x1, playerMesh.position.y, z1),
                new THREE.Vector3(x1, playerMesh.position.y + h, (z1 + deltaZ) / 2),
                new THREE.Vector3(x1, playerMesh.position.y, z1 + deltaZ)
            ];
        } else {
            const z3 = (z2 - z1) / (Math.sqrt((z2 - z1) ** 2 + (x2 - x1) ** 2) / -deltaZ) + z1;
            const x3 = (x2 - x1) / (Math.sqrt((z2 - z1) ** 2 + (x2 - x1) ** 2) / -deltaZ) + x1;
            needMoveX.value = x3 - x1;
            needMoveZ.value = z3 - z1;
            arr = [
                new THREE.Vector3(x1, playerMesh.position.y, z1),
                new THREE.Vector3((x1 + x3) / 2, playerMesh.position.y + h, (z1 + z3) / 2),
                new THREE.Vector3(x3, playerMesh.position.y, z3)
            ];
        }
    }
    const curve = new THREE.CatmullRomCurve3(arr);
    return curve;
};
// 是否需要斜着移动，原来的路线判断不出来，计算路线的时候调整
const needMoveX = ref<number>(0);
const needMoveZ = ref<number>(0);
// 相机、玩家移动
const playerMove = (deltaX: number, deltaZ: number, playerMesh: any, camera: any) => {
    let timer: any;
    const totalStep = Math.floor(Math.max(deltaX, Math.abs(deltaZ)));
    // 样条曲线
    const curve = generateCatmullRomCurve3(deltaX, deltaZ, totalStep);
    const geometry = new THREE.BufferGeometry();
    geometry.setFromPoints(curve.getPoints(totalStep));
    const material = new THREE.LineBasicMaterial({ color: 'cyan' });
    const curveMesh = new THREE.Line(geometry, material);
    scene.add(curveMesh);

    return new Promise(resolve => {
        let num = 0;
        timer = setInterval(() => {
            // 移动主角
            playerMesh.position.x += needMoveX.value / totalStep;
            playerMesh.position.z += needMoveZ.value / totalStep;
            // 更改仓库中储存的主角位置
            playerPosition.value[0] += needMoveX.value / totalStep;
            playerPosition.value[2] += needMoveZ.value / totalStep;

            playerMesh.position.y = curve.getPoints(totalStep)[num].y;
            camera.position.set(playerMesh.position.x - 300, 500, playerMesh.position.z + 200);
            const [x, y, z] = Object.values(playerMesh.position) as [number, number, number];
            if (isCameraYChange.value) {
                camera.lookAt(x + 300, y, z - 300);
            } else {
                camera.lookAt(x + 300, 0, z - 300);
            }
            pointLight.position.set(playerMesh.position.x - 200, 300, playerMesh.position.z + 100);
            num += 1;
            if (num > totalStep) {
                scene.remove(curveMesh);
                clearInterval(timer);
                resolve('ok');
            }
        }, 1);
    });
};
// 失败事件
const failEvent = () => {
    isFailTipShow.value = false;
    restart();
};
// 充值复活
const reCharge = () => {
    isFailTipShow.value = false;
    const x = boxAttrArr.value[2].position[0];
    const z = boxAttrArr.value[2].position[2];
    playerPosition.value[0] = x;
    playerPosition.value[2] = z;
    scene.clear();
    initAdd();
    message.success('复活成功');
};

// 重置
const restart = () => {
    reset();
    scene.clear();
    initAdd();
};

function animate() {
    if (isIncreasingRange.value) {
        range.value += 3;
        if (playerMesh.position.y > 35) {
            playerMesh.position.y -= 0.2;
            playerMesh.scale.y -= 0.4 / 50;
        }
    } else {
        playerMesh.scale.y = 1;
    }
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

// 窗口缩放事件
const windowResize = () => {
    minWidthOrHeight.value = Math.min(window.innerWidth, window.innerHeight - 100) - 80;
    renderer.setSize(minWidthOrHeight.value, minWidthOrHeight.value);
};
onMounted(() => {
    container.value!.appendChild(renderer.domElement);
    // container.value!.ondblclick = () => {
    //     if (document.fullscreenElement) {
    //         document.exitFullscreen();
    //     } else {
    //         container.value!.requestFullscreen();
    //     }
    // };
    // 监听窗口缩放
    window.addEventListener('resize', windowResize);
});
onBeforeUnmount(() => {
    window.removeEventListener('resize', windowResize);
});

const saveAsImage = () => {
    renderer.render(scene, camera);
    const data = renderer.domElement.toDataURL();
    const a = document.createElement('a');
    a.href = data;
    a.download = 'download.png';
    a.click();
    a.remove();
};
const clipToClipBoard = () => {
    renderer.render(scene, camera);
    renderer.domElement.toBlob((blob: any) => {
        const data = [new ClipboardItem({ [blob.type]: blob })];
        navigator.clipboard
            .write(data)
            .then(() => {
                message.success('复制成功');
            })
            .catch(() => {
                message.error('复制失败');
            });
    });
};
</script>

<style scoped>
.outer {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .card {
        width: 100%;
        max-width: 600px;
        height: 80px;
        transition: all 0.3s linear;
    }

    .jump-container {
        width: v-bind(minWidthOrHeight);
        height: v-bind(minWidthOrHeight);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
}
</style>
