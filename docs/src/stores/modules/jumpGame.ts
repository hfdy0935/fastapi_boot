import {ref} from 'vue';
import {defineStore} from 'pinia';
import * as THREE from 'three';

function jumpStore() {
    // 分数
    const score = ref(0);
    // 显示方块的数组
    const boxAttrArr = ref<BoxAttrType[]>(new Array(3).fill(''));
    // 跳的过程中相机是否随主角上下运动
    const isCameraYChange = ref<boolean>(false);

    // 生成方块
    const createNextBox = () => {
        // 上一个的属性
        const oldMesh = boxAttrArr.value[boxAttrArr.value.length - 1];
        const [x, y, z] = oldMesh.position;
        const [width, height, depth] = oldMesh.geometry;

        const newWidth = Math.random() * 100 + 80;
        const newDepth = Math.random() * 100 + 80;
        const geometry = new THREE.BoxGeometry(newWidth, height, newDepth);
        const material = new THREE.MeshPhysicalMaterial({
            color: `rgb(${Math.floor(Math.random() * 256)},${Math.floor(Math.random() * 256)},${Math.floor(Math.random() * 256)})`
        });
        const mesh = new THREE.Mesh(geometry, material);
        // 随机距离
        const distance = Math.random() * 200 + 40;
        // 随机方向
        const direction = Math.random() > 0.5;
        // 计算生成的位置
        const newX = direction ? x + width / 2 + distance + newWidth / 2 : x;
        const newZ = direction ? z : z - depth / 2 - distance - newDepth / 2;
        mesh.position.set(newX, y, newZ);
        mesh.name = 'pathBox';
        return mesh;
    };
    // 初始化
    const initBoxAttrArr = () => {
        // 第一个
        const geometry = new THREE.BoxGeometry(100, 50, 100);
        const material = new THREE.MeshPhysicalMaterial({color: 'deepskyblue'});
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(0, 0, 0);
        boxAttrArr.value[2] = {
            geometry: [100, 50, 100],
            color: 'deepskyblue',
            position: [0, 0, 0]
        };
        // 第二第三个
        const nextMesh = createNextBox();
        const {width: width1, height: height1, depth: depth1} = nextMesh.geometry.parameters;
        boxAttrArr.value.push({
            geometry: [width1, height1, depth1],
            color: nextMesh.material.color,
            position: [...Object.values(nextMesh.position)] as [number, number, number]
        });
        const nextNextMesh = createNextBox();
        const {width: width2, height: height2, depth: depth2} = nextNextMesh.geometry.parameters;
        boxAttrArr.value.push({
            geometry: [width2, height2, depth2],
            color: nextNextMesh.material.color,
            position: [...Object.values(nextNextMesh.position)] as [number, number, number]
        });
    };
    initBoxAttrArr();

    // 主角位置
    const playerPosition = ref<[number, number, number]>([0, 50, 0]);

    // 把新方块的属性添加到数组
    const addBoxAttrToArr = (mesh: any) => {
        const {width, height, depth} = mesh.geometry.parameters;
        boxAttrArr.value.push({
            geometry: [width, height, depth],
            color: mesh.material.color,
            position: [...Object.values(mesh.position)] as [number, number, number]
        });
    };
    const shiftBoxAttrArr = () => {
        boxAttrArr.value.shift();
    };

    // 重置
    const reset = () => {
        // @ts-ignore
        boxAttrArr.value = ['', '', ''];
        initBoxAttrArr();
        score.value = 0;
        playerPosition.value = [0, 50, 0];
    };

    return {playerPosition, score, boxAttrArr, isCameraYChange, createNextBox, addBoxAttrToArr, shiftBoxAttrArr, reset};
}


export const useJumpGameStore = defineStore(
    'jumpGame',
    jumpStore,
    {
        persist: {
            storage: sessionStorage
        }
    }
);

export interface BoxAttrType {
    geometry: [number, number, number];
    color: string | THREE.Color;
    position: [number, number, number];
}