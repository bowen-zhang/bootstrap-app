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

await initializeCurrentUser();

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


export async function refreshCurrentUser() {
  try {
    const response = await getAccountService().getCurrentUser({});
    setCurrentUser({
      id: response.accountId,
      email: response.email,
      firstName: response.firstName,
      lastName: response.lastName,
    });
  } catch (error) {
    clearCurrentUser();
  }
}

// Internal functions

function loadCurrentUser(): CurrentUser | null {
  const raw = localStorage.getItem('currentUser');
  if (!raw)
    return null;

  try {
    return JSON.parse(raw) as CurrentUser;
  } catch (error) {
    console.error('Failed to parse current user from localStorage', error);
    return null;
  }
}

function setCurrentUser(user: CurrentUser ): CurrentUser {
  currentUser.value = user;
  localStorage.setItem('currentUser', JSON.stringify(user));
  return user;
}

function clearCurrentUser() {
  currentUser.value = null;
  localStorage.removeItem('currentUser');
}

async function initializeCurrentUser() {
  const user = loadCurrentUser();
  if (user) {
    setCurrentUser(user);
    return;
  } else {
    await refreshCurrentUser();
  }
}
