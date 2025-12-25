import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/auth_service.dart';
import '../services/analytics_service.dart';

/// Provider for the AuthService instance
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

/// Provider for the AnalyticsService instance
final analyticsServiceProvider = Provider<AnalyticsService>((ref) {
  return AnalyticsService();
});

/// Stream provider for auth state changes
final authStateProvider = StreamProvider<User?>((ref) {
  final authService = ref.watch(authServiceProvider);
  return authService.authStateChanges;
});

/// Provider for current user
final currentUserProvider = Provider<User?>((ref) {
  return ref.watch(authStateProvider).value;
});

/// Provider to check if user is logged in
final isLoggedInProvider = Provider<bool>((ref) {
  final user = ref.watch(currentUserProvider);
  return user != null;
});

/// Provider to check if user is anonymous
final isAnonymousProvider = Provider<bool>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.isAnonymous ?? true;
});

/// Provider for user display name
final userDisplayNameProvider = Provider<String>((ref) {
  final user = ref.watch(currentUserProvider);
  if (user == null) return 'Guest';
  if (user.isAnonymous) return 'Guest User';
  return user.displayName ?? user.email ?? 'User';
});

/// Provider for user email
final userEmailProvider = Provider<String?>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.email;
});

/// Provider for user photo URL
final userPhotoUrlProvider = Provider<String?>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.photoURL;
});

/// Provider for user ID
final userIdProvider = Provider<String?>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.uid;
});

/// Auth state notifier for managing auth actions
class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final AuthService _authService;
  final AnalyticsService _analyticsService;

  AuthNotifier(this._authService, this._analyticsService)
    : super(const AsyncValue.loading()) {
    // Listen to auth changes
    _authService.authStateChanges.listen((user) {
      state = AsyncValue.data(user);
    });
  }

  Future<void> signInWithGoogle() async {
    state = const AsyncValue.loading();
    try {
      final result = await _authService.signInWithGoogle();
      if (result != null) {
        await _analyticsService.trackLogin(method: 'google');
        await _analyticsService.startSession();
      }
      state = AsyncValue.data(result?.user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> signInWithEmail(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final result = await _authService.signInWithEmail(email, password);
      await _analyticsService.trackLogin(method: 'email');
      await _analyticsService.startSession();
      state = AsyncValue.data(result.user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> signUpWithEmail(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final result = await _authService.signUpWithEmail(email, password);
      await _analyticsService.trackSignup(method: 'email');
      await _analyticsService.startSession();
      state = AsyncValue.data(result.user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> signInAnonymously() async {
    state = const AsyncValue.loading();
    try {
      final result = await _authService.signInAnonymously();
      await _analyticsService.trackLogin(method: 'anonymous');
      await _analyticsService.startSession();
      state = AsyncValue.data(result.user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> signOut() async {
    try {
      await _analyticsService.trackLogout();
      await _analyticsService.endSession();
      await _authService.signOut();
      state = const AsyncValue.data(null);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

/// Provider for auth notifier
final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
      final authService = ref.watch(authServiceProvider);
      final analyticsService = ref.watch(analyticsServiceProvider);
      return AuthNotifier(authService, analyticsService);
    });
