<template>
	<Teleport to="body">
		<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-lg bg-cyan-100 dark:bg-cyan-900/30 flex items-center justify-center">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-cyan-600 dark:text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
							</svg>
						</div>
						<div>
							<h2 class="text-lg font-semibold text-slate-900 dark:text-white">User Management</h2>
							<p class="text-xs text-slate-500 dark:text-slate-400">Manage users and invitations</p>
						</div>
					</div>
					<button
						@click="$emit('close')"
						class="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Tabs -->
				<div class="flex border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/30">
					<button
						@click="switchTab('users')"
						:class="[
							'px-6 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
							activeTab === 'users' 
								? 'border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-white dark:bg-slate-800' 
								: 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
						]"
					>
						Users
					</button>
					<button
						@click="switchTab('invites')"
						:class="[
							'px-6 py-3 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-2',
							activeTab === 'invites' 
								? 'border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-white dark:bg-slate-800' 
								: 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
						]"
					>
						Invitations
						<span v-if="pendingInvites.length > 0" class="px-1.5 py-0.5 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full tabular-nums">
							{{ pendingInvites.length }}
						</span>
					</button>
				</div>

				<!-- Content -->
				<div class="flex-1 overflow-auto p-6">
					<!-- Users Tab -->
					<template v-if="activeTab === 'users'">
						<!-- Add User Button -->
						<div class="mb-6">
							<button
								@click="showAddUser = true"
								class="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
							>
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
								</svg>
								Add User
							</button>
						</div>

					<!-- Loading State -->
					<div v-if="isLoading" class="flex items-center justify-center py-12">
						<svg class="animate-spin h-8 w-8 text-cyan-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
					</div>

					<!-- Users List -->
					<div v-else class="space-y-3">
						<div
							v-for="u in users"
							:key="u.id"
							class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700"
						>
						<div class="flex items-center gap-4">
							<!-- Avatar -->
							<div 
								class="w-10 h-10 rounded-full flex items-center justify-center text-white font-medium"
								:class="u.role === 'owner' ? 'bg-gradient-to-br from-amber-500 to-orange-600' : 'bg-gradient-to-br from-cyan-500 to-blue-600'"
							>
								{{ u.first_name.charAt(0).toUpperCase() }}
							</div>
							
							<div>
								<div class="flex items-center gap-2">
									<span class="font-medium text-slate-900 dark:text-white">
										{{ getFullName(u) }}
									</span>
									<span :class="getRoleBadgeClass(u.role)" class="text-xs px-2 py-0.5 rounded-full">
										{{ getRoleLabel(u.role) }}
									</span>
								</div>
								<div class="text-sm text-slate-500 dark:text-slate-400">
									{{ u.email }}
									<span v-if="u.last_login" class="ml-2">
										• Last login: {{ formatDate(u.last_login) }}
									</span>
								</div>
							</div>
						</div>

							<!-- Actions -->
							<div v-if="u.role !== 'owner'" class="flex items-center gap-2">
								<button
									@click="editUser(u)"
									class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700"
									title="Edit user"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
								</button>
								<button
									@click="confirmDelete(u)"
									class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30"
									title="Delete user"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
							<div v-else class="text-xs text-slate-400 italic">
								Cannot modify owner
							</div>
						</div>

						<div v-if="users.length === 0" class="text-center py-12 text-slate-500">
							No users found
						</div>
					</div>
					</template>

					<!-- Invitations Tab -->
					<template v-else-if="activeTab === 'invites'">
						<!-- Invite Button -->
						<div class="mb-6">
							<button
								@click="openInviteForm"
								class="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
							>
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
								Send Invitation
							</button>
						</div>

						<!-- Loading State -->
						<div v-if="isLoadingInvites" class="flex items-center justify-center py-12">
							<svg class="animate-spin h-8 w-8 text-cyan-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						</div>

						<template v-else>
							<!-- Pending Invitations -->
							<div v-if="pendingInvites.length > 0" class="mb-6">
								<h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">Pending Invitations</h3>
								<div class="space-y-2">
									<div
										v-for="invite in pendingInvites"
										:key="invite.id"
										class="flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-900/10 rounded-lg border border-amber-200 dark:border-amber-800/30"
									>
										<div class="flex items-center gap-3">
											<div class="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white font-medium">
												<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
												</svg>
											</div>
											<div>
												<div class="flex items-center gap-2">
													<span class="font-medium text-slate-900 dark:text-white">{{ invite.email }}</span>
													<span :class="getRoleBadgeClass(invite.role)" class="text-xs px-2 py-0.5 rounded-full">
														{{ getRoleLabel(invite.role) }}
													</span>
												</div>
												<div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
													Sent {{ formatRelativeDate(invite.created_at) }} • Expires in {{ formatExpiresIn(invite.expires_at) }}
												</div>
											</div>
										</div>
										<div class="flex items-center gap-2">
											<button
												@click="onResendInvite(invite)"
												class="p-2 text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 rounded-lg hover:bg-white dark:hover:bg-slate-800"
												title="Resend invitation"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
												</svg>
											</button>
											<button
												@click="confirmRevokeInvite(invite)"
												class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
												title="Revoke invitation"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
												</svg>
											</button>
										</div>
									</div>
								</div>
							</div>

							<!-- Past Invitations -->
							<div v-if="pastInvites.length > 0">
								<h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">History</h3>
								<div class="space-y-2">
									<div
										v-for="invite in pastInvites"
										:key="invite.id"
										class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900/30 rounded-lg border border-slate-200 dark:border-slate-700 opacity-60"
									>
										<div class="flex items-center gap-3">
											<div class="text-sm text-slate-600 dark:text-slate-400">{{ invite.email }}</div>
											<span :class="getInviteStatusClass(invite.status)" class="text-xs px-2 py-0.5 rounded-full">
												{{ getInviteStatusLabel(invite.status) }}
											</span>
										</div>
										<div class="text-xs text-slate-400">
											{{ formatRelativeDate(invite.created_at) }}
										</div>
									</div>
								</div>
							</div>

							<!-- Empty State -->
							<div v-if="invites.length === 0" class="text-center py-12 text-slate-500">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
								<p>No invitations sent yet</p>
								<p class="text-sm mt-1">Click "Send Invitation" to invite users via email</p>
							</div>
						</template>
					</template>
				</div>
			</div>
		</div>

		<!-- Add/Edit User Modal -->
		<div v-if="showAddUser || editingUser" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">
					{{ editingUser ? 'Edit User' : 'Add New User' }}
				</h3>
				
				<form @submit.prevent="onSubmitUser" class="space-y-4">
					<!-- Send Invitation Toggle (only for new users) -->
					<div v-if="!editingUser" class="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
						<label class="flex items-center justify-between cursor-pointer">
							<div class="flex items-center gap-2">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
								<span class="text-sm font-medium text-slate-700 dark:text-slate-300">Send invitation email</span>
							</div>
							<button 
								type="button"
								@click="userForm.sendInvite = !userForm.sendInvite"
								class="relative w-10 h-6 rounded-full transition-colors"
								:class="userForm.sendInvite ? 'bg-cyan-500' : 'bg-slate-300 dark:bg-slate-600'"
							>
								<span class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform" :class="userForm.sendInvite ? 'translate-x-4' : ''"></span>
							</button>
						</label>
						<p class="text-xs text-slate-500 mt-2">
							{{ userForm.sendInvite 
								? 'User will receive an email to set up their account' 
								: 'You will set the password for this user' 
							}}
						</p>
					</div>

					<!-- Email (always required) -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Email
						</label>
						<input
							v-model="userForm.email"
							type="email"
							required
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="user@example.com"
						/>
					</div>

					<!-- Role (always required) -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Role
						</label>
						<select
							v-model="userForm.role"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
						>
							<option value="readonly">Read Only - Can only view the network map</option>
							<option value="readwrite">Read/Write - Can view and modify the network map</option>
						</select>
					</div>

					<!-- Fields only shown when NOT sending invite (creating user directly) -->
					<template v-if="!userForm.sendInvite || editingUser">
						<div v-if="!editingUser">
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								Username
							</label>
							<input
								v-model="userForm.username"
								type="text"
								required
								pattern="^[a-zA-Z][a-zA-Z0-9_-]*$"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
								placeholder="username"
							/>
						</div>
						
						<!-- First Name / Last Name -->
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
									First Name
								</label>
								<input
									v-model="userForm.firstName"
									type="text"
									required
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
									placeholder="John"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
									Last Name
								</label>
								<input
									v-model="userForm.lastName"
									type="text"
									required
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
									placeholder="Doe"
								/>
							</div>
						</div>
						
						<div v-if="!editingUser">
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								Password
							</label>
							<input
								v-model="userForm.password"
								type="password"
								required
								minlength="8"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
								placeholder="••••••••"
							/>
							<p class="mt-1 text-xs text-slate-500">Minimum 8 characters</p>
						</div>

						<div v-if="editingUser">
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								New Password <span class="text-slate-400">(leave blank to keep current)</span>
							</label>
							<input
								v-model="userForm.password"
								type="password"
								minlength="8"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
								placeholder="••••••••"
							/>
						</div>
					</template>

					<div v-if="formError" class="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-500/50 rounded-lg">
						<p class="text-sm text-red-600 dark:text-red-400">{{ formError }}</p>
					</div>

					<div class="flex gap-3 pt-2">
						<button
							type="button"
							@click="closeUserForm"
							class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
						>
							Cancel
						</button>
						<button
							type="submit"
							:disabled="isSubmitting"
							class="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50"
						>
							<template v-if="isSubmitting">Saving...</template>
							<template v-else-if="editingUser">Update User</template>
							<template v-else-if="userForm.sendInvite">Send Invitation</template>
							<template v-else>Create User</template>
						</button>
					</div>
				</form>
			</div>
		</div>

		<!-- Delete Confirmation Modal -->
		<div v-if="deletingUser" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">Delete User</h3>
				<p class="text-slate-600 dark:text-slate-400 mb-6">
					Are you sure you want to delete <strong>{{ getFullName(deletingUser) }}</strong>? 
					This action cannot be undone.
				</p>
				
				<div class="flex gap-3">
					<button
						@click="deletingUser = null"
						class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
					>
						Cancel
					</button>
					<button
						@click="onDeleteUser"
						:disabled="isSubmitting"
						class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
					>
						{{ isSubmitting ? 'Deleting...' : 'Delete User' }}
					</button>
				</div>
			</div>
		</div>

		<!-- Invite User Modal -->
		<div v-if="showInviteForm" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Send Invitation</h3>
				
				<form @submit.prevent="onSubmitInvite" class="space-y-4">
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Email Address
						</label>
						<input
							v-model="inviteForm.email"
							type="email"
							required
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="user@example.com"
						/>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Role
						</label>
						<select
							v-model="inviteForm.role"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
						>
							<option value="readonly">Read Only - Can only view the network map</option>
							<option value="readwrite">Read/Write - Can view and modify the network map</option>
						</select>
					</div>

					<div class="p-3 bg-slate-100 dark:bg-slate-900 rounded-lg">
						<p class="text-sm text-slate-600 dark:text-slate-400">
							An email will be sent with a link to create their account. The invitation expires in 72 hours.
						</p>
					</div>

					<div v-if="inviteFormError" class="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-500/50 rounded-lg">
						<p class="text-sm text-red-600 dark:text-red-400">{{ inviteFormError }}</p>
					</div>

					<div class="flex gap-3 pt-2">
						<button
							type="button"
							@click="closeInviteForm"
							class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
						>
							Cancel
						</button>
						<button
							type="submit"
							:disabled="isSubmittingInvite"
							class="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50"
						>
							{{ isSubmittingInvite ? 'Sending...' : 'Send Invitation' }}
						</button>
					</div>
				</form>
			</div>
		</div>

		<!-- Revoke Invitation Confirmation Modal -->
		<div v-if="revokingInvite" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">Revoke Invitation</h3>
				<p class="text-slate-600 dark:text-slate-400 mb-6">
					Are you sure you want to revoke the invitation for <strong>{{ revokingInvite.email }}</strong>? 
					They will no longer be able to use the invitation link.
				</p>
				
				<div class="flex gap-3">
					<button
						@click="revokingInvite = null"
						class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
					>
						Cancel
					</button>
					<button
						@click="onRevokeInvite"
						:disabled="isSubmittingInvite"
						class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
					>
						{{ isSubmittingInvite ? 'Revoking...' : 'Revoke Invitation' }}
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from "vue";
import { useAuth } from "../composables/useAuth";
import type { User, UserRole, Invite, InviteStatus } from "../types/auth";
import { getRoleLabel, getFullName, getInviteStatusLabel, getInviteStatusClass } from "../types/auth";

defineEmits<{
	(e: "close"): void;
}>();

const { listUsers, createUser, updateUser, deleteUser, listInvites, createInvite, revokeInvite, resendInvite } = useAuth();

// Tab state
const activeTab = ref<"users" | "invites">("users");

// Users state
const users = ref<User[]>([]);
const isLoading = ref(true);
const isSubmitting = ref(false);
const formError = ref<string | null>(null);

const showAddUser = ref(false);
const editingUser = ref<User | null>(null);
const deletingUser = ref<User | null>(null);

const userForm = ref({
	username: "",
	firstName: "",
	lastName: "",
	email: "",
	role: "readonly" as UserRole,
	password: "",
	sendInvite: true, // Default to sending invitation
});

// Invites state
const invites = ref<Invite[]>([]);
const isLoadingInvites = ref(false);
const showInviteForm = ref(false);
const inviteFormError = ref<string | null>(null);
const isSubmittingInvite = ref(false);
const revokingInvite = ref<Invite | null>(null);

const inviteForm = ref({
	email: "",
	role: "readonly" as UserRole,
});

// Computed
const pendingInvites = computed(() => invites.value.filter(i => i.status === "pending"));
const pastInvites = computed(() => invites.value.filter(i => i.status !== "pending"));

async function loadUsers() {
	isLoading.value = true;
	try {
		users.value = await listUsers();
	} catch (e) {
		console.error("Failed to load users:", e);
	} finally {
		isLoading.value = false;
	}
}

onMounted(() => {
	loadUsers();
});

function getRoleBadgeClass(role: UserRole): string {
	switch (role) {
		case "owner":
			return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400";
		case "readwrite":
			return "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400";
		case "readonly":
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
		default:
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
	}
}

function formatDate(dateStr: string): string {
	const date = new Date(dateStr);
	return date.toLocaleDateString(undefined, { 
		month: "short", 
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit"
	});
}

function editUser(user: User) {
	editingUser.value = user;
	userForm.value = {
		username: user.username,
		firstName: user.first_name,
		lastName: user.last_name,
		email: user.email,
		role: user.role,
		password: "",
		sendInvite: false,
	};
	formError.value = null;
}

function confirmDelete(user: User) {
	deletingUser.value = user;
}

function closeUserForm() {
	showAddUser.value = false;
	editingUser.value = null;
	userForm.value = {
		username: "",
		firstName: "",
		lastName: "",
		email: "",
		role: "readonly",
		password: "",
		sendInvite: true,
	};
	formError.value = null;
}

async function onSubmitUser() {
	formError.value = null;
	isSubmitting.value = true;

	try {
		if (editingUser.value) {
			// Update existing user
			await updateUser(editingUser.value.id, {
				first_name: userForm.value.firstName,
				last_name: userForm.value.lastName,
				email: userForm.value.email,
				role: userForm.value.role,
				password: userForm.value.password || undefined,
			});
			closeUserForm();
			await loadUsers();
		} else if (userForm.value.sendInvite) {
			// Send invitation instead of creating user directly
			await createInvite({
				email: userForm.value.email,
				role: userForm.value.role,
			});
			closeUserForm();
			// Refresh invites list and switch to invites tab
			await loadInvites();
			activeTab.value = "invites";
		} else {
			// Create new user directly (with password)
			await createUser({
				username: userForm.value.username,
				first_name: userForm.value.firstName,
				last_name: userForm.value.lastName,
				email: userForm.value.email,
				password: userForm.value.password,
				role: userForm.value.role,
			});
			closeUserForm();
			await loadUsers();
		}
	} catch (e: any) {
		formError.value = e.message || "Failed to save user";
	} finally {
		isSubmitting.value = false;
	}
}

async function onDeleteUser() {
	if (!deletingUser.value) return;
	
	isSubmitting.value = true;
	try {
		await deleteUser(deletingUser.value.id);
		deletingUser.value = null;
		await loadUsers();
	} catch (e: any) {
		alert(e.message || "Failed to delete user");
	} finally {
		isSubmitting.value = false;
	}
}

// ==================== Invite Management ====================

async function loadInvites() {
	isLoadingInvites.value = true;
	try {
		invites.value = await listInvites();
	} catch (e) {
		console.error("Failed to load invites:", e);
	} finally {
		isLoadingInvites.value = false;
	}
}

function openInviteForm() {
	inviteForm.value = { email: "", role: "readonly" };
	inviteFormError.value = null;
	showInviteForm.value = true;
}

function closeInviteForm() {
	showInviteForm.value = false;
	inviteForm.value = { email: "", role: "readonly" };
	inviteFormError.value = null;
}

async function onSubmitInvite() {
	inviteFormError.value = null;
	isSubmittingInvite.value = true;
	
	try {
		await createInvite({
			email: inviteForm.value.email,
			role: inviteForm.value.role,
		});
		closeInviteForm();
		await loadInvites();
	} catch (e: any) {
		inviteFormError.value = e.message || "Failed to send invitation";
	} finally {
		isSubmittingInvite.value = false;
	}
}

function confirmRevokeInvite(invite: Invite) {
	revokingInvite.value = invite;
}

async function onRevokeInvite() {
	if (!revokingInvite.value) return;
	
	isSubmittingInvite.value = true;
	try {
		await revokeInvite(revokingInvite.value.id);
		revokingInvite.value = null;
		await loadInvites();
	} catch (e: any) {
		alert(e.message || "Failed to revoke invitation");
	} finally {
		isSubmittingInvite.value = false;
	}
}

async function onResendInvite(invite: Invite) {
	try {
		await resendInvite(invite.id);
		alert("Invitation email resent successfully");
	} catch (e: any) {
		alert(e.message || "Failed to resend invitation");
	}
}

function formatRelativeDate(dateStr: string): string {
	const date = new Date(dateStr);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffMins = Math.floor(diffMs / 60000);
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);
	
	if (diffMins < 1) return "just now";
	if (diffMins < 60) return `${diffMins}m ago`;
	if (diffHours < 24) return `${diffHours}h ago`;
	if (diffDays < 7) return `${diffDays}d ago`;
	
	return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatExpiresIn(dateStr: string): string {
	const date = new Date(dateStr);
	const now = new Date();
	const diffMs = date.getTime() - now.getTime();
	
	if (diffMs <= 0) return "expired";
	
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);
	
	if (diffHours < 1) return "< 1 hour";
	if (diffHours < 24) return `${diffHours}h`;
	return `${diffDays}d`;
}

// Load invites when tab changes
function switchTab(tab: "users" | "invites") {
	activeTab.value = tab;
	if (tab === "invites" && invites.value.length === 0) {
		loadInvites();
	}
}
</script>
