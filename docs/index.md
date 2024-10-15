---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
    name: 'FastApiBoot'
    text: 'FastAPI项目启动器'
    image:
        src: /logo.svg
        alt: FastApiBoot
    actions:
        - theme: brand
          text: 开始
          link: /tutorial/v1/hello_world
        - theme: alt
          text: APIs
          link: /api/v1

features:
    - icon:
          src: /jump.png
      title: 跳一跳
      details: 进来玩会吗？
      link: /jumpGame
    - icon:
          src: /IOC.png
      title: IOC
      details: 项目扫描，控制反转，自动装配
    - icon:
          src: /CBV.png
      title: CBV
      details: 类视图，层级结构更清晰

    - icon:
          src: /MVC.png
      title: MVC
      details: 模块化， Model View Controller
---

<style>
:root {
  --vp-home-hero-name-color: transparent;
  --vp-home-hero-name-background: -webkit-linear-gradient(120deg, #00AB67, #41d1ff);
}

</style>
