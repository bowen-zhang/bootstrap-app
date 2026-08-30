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

export const currentUser = ref<CurrentUser | null>(null);

export async function refreshCurrentUser(): Promise<void> {
  try {
    const response = await getAccountService().getCurrentUser({});
    setCurrentUser({
      id: response.accountId,
      email: response.email,
      firstName: response.firstName,
      lastName: response.lastName,
    });
  } catch (error) {
    console.error('Failed to refresh current user', error);
    await logout();
  }
}

export async function login(email: string, password: string) {
    const response = await getAccountService().login({
      email,
      password,
    });

    setCurrentUser({
      id: response.accountId,
      email: response.email,
      firstName: response.firstName,
      lastName: response.lastName,
    });
    await router.push('/');
}

export async function logout() {
  try {
    await getAccountService().logout({});
  } catch (error) {
    console.error('Logout failed', error);
  } finally {
    clearCurrentUser();
    await router.push('/login');
  }
}

// Internal functions

function setCurrentUser(user: CurrentUser ): CurrentUser {
  currentUser.value = user;
  localStorage.setItem('currentUser', JSON.stringify(user));
  return user;
}

function clearCurrentUser() {
  currentUser.value = null;
  localStorage.removeItem('currentUser');
}