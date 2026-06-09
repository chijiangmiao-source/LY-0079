import { redirect } from '@sveltejs/kit';
import { browser } from '$app/environment';
import { isAuthenticated } from '$lib/utils/auth';

export function load({ url }) {
  if (browser && !url.pathname.startsWith('/login')) {
    if (!isAuthenticated()) {
      throw redirect(302, '/login');
    }
  }
  return {};
}
