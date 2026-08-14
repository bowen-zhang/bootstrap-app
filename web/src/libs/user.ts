import { computed } from 'vue'
import { getAccountService } from '@/libs/api'
import router from '@/router'
import { ref } from 'vue'

type CurrentUser = {
  id: string
  email: string
  firstName: string
  lastName: string
}

function loadCurrentUser(): CurrentUser | null {
  const raw = localStorage.getItem('currentUser');
  if (!raw) return null;

  try {
    return JSON.parse(raw) as CurrentUser;
  } catch {
    return null;
  }
}
export const currentUser = ref<CurrentUser | null>(loadCurrentUser());

export async function login(email: string, password: string) {
    const response = await getAccountService().login({
      email,
      password,
    });

    currentUser.value = {
      id: response.accountId,
      email: response.email,
      firstName: response.firstName,
      lastName: response.lastName,
    };
    localStorage.setItem('currentUser', JSON.stringify(currentUser.value));
    await router.push('/');
}

export async function logout() {
  try {
    await getAccountService().logout({});
  } catch (error) {
    console.error('Logout failed', error);
  } finally {
    currentUser.value = null;
    localStorage.removeItem('currentUser');
    await router.push('/login');
  }
}