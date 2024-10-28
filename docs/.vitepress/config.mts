import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
    base: "/fastapi_boot/", // 仓库名
    title: "FastApiBoot",
    description: "FastAPI项目启动器",
    head: [
        [
            "link",
            {
                rel: "icon",
                href: "favicon.ico",
            },
        ],
    ],
    themeConfig: {
        // https://vitepress.dev/reference/default-theme-config
        logo: "/logo.svg",
        darkModeSwitchLabel: "外观",
        sidebarMenuLabel: "菜单",
        returnToTopLabel: "回到顶部",
        outline: [2, 6],
        outlineTitle: "本页目录",
        lightModeSwitchTitle: "切换为浅色模式",
        darkModeSwitchTitle: "切换为深色模式",
        lastUpdated: {
            // 最后更新时间
            text: "更新于",
            formatOptions: {
                dateStyle: "full",
                timeStyle: "medium",
            },
        },
        search: {
            // 搜索
            provider: "local",
        },
        nav: [
            {
                text: "开始",
                link: "/tutorial/v3",
            },
        ],

        sidebar: [
            {
                text: "v3",
                link: "/tutorial/v3",
            },
            {
                text: "v2",
                link: "/tutorial/v2",
            },
            {
                text: "v1",
                items: [
                    {
                        text: "1. HelloWorld",
                        link: "/tutorial/v1/hello_world",
                    },
                    {
                        text: "2. 控制器和路由映射",
                        link: "/tutorial/v1/controller",
                    },
                    {
                        text: "3. 项目启动和挂载",
                        link: "/tutorial/v1/project.md",
                    },
                    {
                        text: "4. 项目结构",
                        link: "/tutorial/v1/structure.md",
                    },
                    {
                        text: "5. hooks",
                        link: "/tutorial/v1/hooks.md",
                    },
                ],
            },
        ],
        socialLinks: [{ icon: "github", link: "https://github.com/hfdy0935/fastapi_boot" }],
        docFooter: {
            prev: "上一节",
            next: "下一节",
        },
    },
    markdown: {
        // 显示行号
        lineNumbers: true,
        // 图片懒加载
        image: {
            lazyLoading: true,
        },
    },
    lastUpdated: true, // 最后更新时间
});
