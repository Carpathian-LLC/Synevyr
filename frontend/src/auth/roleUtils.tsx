export function hasRole(user: { roles: string[] }, role: string): boolean {
  return user.roles.includes(role);
}

export function hasAnyRole(user: { roles: string[] }, roles: string[]): boolean {
  return roles.some(r => user.roles.includes(r));
}

export function hasPermission(user: { permissions: string[] }, permission: string): boolean {
  return user.permissions.includes(permission);
}

export function hasAnyPermission(user: { permissions: string[] }, permissions: string[]): boolean {
  return permissions.some(p => user.permissions.includes(p));
}
