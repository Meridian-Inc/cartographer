import { createRouter, createWebHistory } from 'vue-router';
import MainApp from './components/MainApp.vue';
import EmbedView from './components/EmbedView.vue';

const routes = [
	{
		path: '/',
		name: 'main',
		component: MainApp
	},
	{
		path: '/embed/:embedId',
		name: 'embed',
		component: EmbedView,
		props: true
	}
];

const router = createRouter({
	history: createWebHistory(),
	routes
});

export default router;
