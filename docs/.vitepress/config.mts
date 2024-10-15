import { defineConfig } from 'vitepress';
import { tutorialNav, tutorialSidebar } from '../tutorial/v1';

// https://vitepress.dev/reference/site-config
export default defineConfig({
    base: '/fastapi_boot/', // 仓库名
    title: 'FastApiBoot',
    description: 'FastAPI项目启动器',
    head: [
        [
            'link',
            {
                rel: 'icon',
                href: 'favicon.ico'
            }
        ]
    ],
    themeConfig: {
        // https://vitepress.dev/reference/default-theme-config
        logo: '/logo.svg',
        darkModeSwitchLabel: '外观',
        sidebarMenuLabel: '菜单',
        returnToTopLabel: '回到顶部',
        outline: [2, 6],
        outlineTitle: '本页目录',
        lightModeSwitchTitle: '切换为浅色模式',
        darkModeSwitchTitle: '切换为深色模式',
        lastUpdated: {
            // 最后更新时间
            text: '更新于',
            formatOptions: {
                dateStyle: 'full',
                timeStyle: 'medium'
            }
        },
        search: {
            // 搜索
            provider: 'local'
        },
        nav: [
            tutorialNav,
            {
                text: 'APIs',
                items: [
                    {
                        text: 'v1',
                        link: '/api/v1'
                    },
                    {
                        text: 'v2',
                        link: '/api/v2'
                    }
                ]
            }
        ],

        sidebar: {
            ...tutorialSidebar
        },
        socialLinks: [{ icon: 'github', link: 'https://github.com/hfdy0935/fastapi_boot' }],
        docFooter: {
            prev: '上一节',
            next: '下一节'
        }
    },
    markdown: {
        // 显示行号
        lineNumbers: true,
        // 图片懒加载
        image: {
            lazyLoading: true
        }
    },
    lastUpdated: true // 最后更新时间
});
