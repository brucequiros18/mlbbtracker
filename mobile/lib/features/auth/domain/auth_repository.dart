import 'account.dart';

/// Account operations. Google is the only sign-in method; the app password is
/// app-only and never used to log in.
abstract interface class AuthRepository {
  /// Whether this server has Google sign-in configured.
  Future<AuthConfig> config();

  /// Exchange a Google ID token for an app session.
  Future<AuthSessionResult> signInWithGoogle(String credential);

  /// Complete the profile: username, self-declared MLBB ID and app password.
  Future<Account> register({
    required String token,
    required String username,
    required String mlbbId,
    required String password,
  });

  /// The account behind a session token.
  Future<Account> me(String token);

  /// Change profile fields; [currentPassword] confirms the change.
  Future<Account> updateProfile({
    required String token,
    String? username,
    String? mlbbId,
    required String currentPassword,
    String? newPassword,
  });

  /// Forget the session on the server.
  Future<void> logout(String token);
}
