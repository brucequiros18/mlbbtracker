import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/local/local_store.dart';
import '../data/auth_repository_impl.dart';
import '../domain/account.dart';
import '../domain/auth_repository.dart';

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepositoryImpl(ref.watch(dioProvider)),
);

/// Server-side sign-in configuration (is Google configured? which client ID?).
final authConfigProvider = FutureProvider<AuthConfig>(
  (ref) => ref.watch(authRepositoryProvider).config(),
);

/// The app-account bearer token, persisted on the device.
final accountTokenProvider =
    StateNotifierProvider<AccountTokenNotifier, String?>(
  (ref) => AccountTokenNotifier(ref.watch(localStoreProvider)),
);

class AccountTokenNotifier extends StateNotifier<String?> {
  AccountTokenNotifier(this._store) : super(_store.readAccountToken());

  final LocalStore _store;

  Future<void> save(String token) async {
    await _store.saveAccountToken(token);
    state = token;
  }

  Future<void> clear() async {
    await _store.clearAccountToken();
    state = null;
  }
}

/// The signed-in account, or null when nobody is signed in.
///
/// An expired or revoked session clears itself, so the app never shows a
/// profile it can no longer prove.
final currentAccountProvider = FutureProvider<Account?>((ref) async {
  final token = ref.watch(accountTokenProvider);
  if (token == null) return null;
  try {
    return await ref.watch(authRepositoryProvider).me(token);
  } on ApiException catch (e) {
    if (e.kind == ApiErrorKind.unauthorized) {
      await ref.read(accountTokenProvider.notifier).clear();
      return null;
    }
    rethrow;
  }
});

sealed class AuthActionState {
  const AuthActionState();
}

class AuthIdle extends AuthActionState {
  const AuthIdle();
}

class AuthBusy extends AuthActionState {
  const AuthBusy();
}

class AuthFailure extends AuthActionState {
  const AuthFailure(this.message);
  final String message;
}

class AuthController extends StateNotifier<AuthActionState> {
  AuthController(this._ref, this._repo, this._tokens) : super(const AuthIdle());

  final Ref _ref;
  final AuthRepository _repo;
  final AccountTokenNotifier _tokens;

  Future<void> signInWithGoogle(String credential) async {
    state = const AuthBusy();
    try {
      final result = await _repo.signInWithGoogle(credential);
      await _tokens.save(result.sessionToken);
      _ref.invalidate(currentAccountProvider);
      state = const AuthIdle();
    } on ApiException catch (e) {
      state = AuthFailure(e.message);
    } catch (_) {
      state = const AuthFailure('Could not reach the server. Please try again.');
    }
  }

  Future<bool> register({
    required String username,
    required String mlbbId,
    required String password,
  }) async {
    final token = _tokens.state;
    if (token == null) {
      state = const AuthFailure('Sign in with Google first.');
      return false;
    }
    state = const AuthBusy();
    try {
      await _repo.register(
        token: token,
        username: username,
        mlbbId: mlbbId,
        password: password,
      );
      _ref.invalidate(currentAccountProvider);
      state = const AuthIdle();
      return true;
    } on ApiException catch (e) {
      state = AuthFailure(e.message);
      return false;
    } catch (_) {
      state = const AuthFailure('Could not reach the server. Please try again.');
      return false;
    }
  }

  Future<bool> updateProfile({
    String? username,
    String? mlbbId,
    required String currentPassword,
    String? newPassword,
  }) async {
    final token = _tokens.state;
    if (token == null) {
      state = const AuthFailure('Sign in with Google first.');
      return false;
    }
    state = const AuthBusy();
    try {
      await _repo.updateProfile(
        token: token,
        username: username,
        mlbbId: mlbbId,
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      _ref.invalidate(currentAccountProvider);
      state = const AuthIdle();
      return true;
    } on ApiException catch (e) {
      state = AuthFailure(e.message);
      return false;
    } catch (_) {
      state = const AuthFailure('Could not reach the server. Please try again.');
      return false;
    }
  }

  Future<void> signOut() async {
    final token = _tokens.state;
    if (token != null) {
      try {
        await _repo.logout(token);
      } on ApiException {
        // Local sign-out must succeed even if the server call fails.
      }
    }
    await _tokens.clear();
    _ref.invalidate(currentAccountProvider);
    state = const AuthIdle();
  }

  /// Surface a failure that happened before the backend was called (for
  /// example a Google popup that could not open).
  void fail(String message) => state = AuthFailure(message);

  void clearError() => state = const AuthIdle();
}

final authControllerProvider =
    StateNotifierProvider.autoDispose<AuthController, AuthActionState>(
  (ref) => AuthController(
    ref,
    ref.watch(authRepositoryProvider),
    ref.watch(accountTokenProvider.notifier),
  ),
);
