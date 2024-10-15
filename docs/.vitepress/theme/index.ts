// https://vitepress.dev/guide/custom-theme
import type { Theme } from 'vitepress';
import DefaultTheme from 'vitepress/theme';
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';

export default {
    extends: DefaultTheme,
    enhanceApp({ app, router, siteData }) {
        // ...
        const pinia = createPinia();
        pinia.use(piniaPluginPersistedstate);
        app.use(pinia);
        // app.use(Antd);
    }
} satisfies Theme;
