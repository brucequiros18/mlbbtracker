/// An MLBB Tracker account, created by signing in with Google.
///
/// Google is the only credential. [username], [mlbbId] and the app password
/// are app-only profile data:
///
/// * [mlbbId] is **self-declared** - typed in by the player, never checked
///   against Moonton, which is why [mlbbIdVerified] is always false;
/// * the password is stored as a hash on the server and never used to sign in.
class Account {
  const Account({
    required this.id,
    required this.email,
    this.googleName,
    this.pictureUrl,
    this.username,
    this.mlbbId,
    required this.profileComplete,
    required this.mlbbIdVerified,
    this.createdAt,
    this.lastLoginAt,
  });

  final int id;
  final String email;
  final String? googleName;
  final String? pictureUrl;
  final String? username;
  final String? mlbbId;
  final bool profileComplete;
  final bool mlbbIdVerified;
  final DateTime? createdAt;
  final DateTime? lastLoginAt;

  /// What to call the player: the chosen username, else the Google name.
  String get displayName => username ?? googleName ?? email;

  String get initials {
    final source = displayName.trim();
    if (source.isEmpty) return '?';
    return String.fromCharCode(source.runes.first).toUpperCase();
  }

  factory Account.fromJson(Map<String, dynamic> json) {
    return Account(
      id: (json['id'] as num).toInt(),
      email: json['email'] as String? ?? '',
      googleName: json['googleName'] as String?,
      pictureUrl: json['pictureUrl'] as String?,
      username: json['username'] as String?,
      mlbbId: json['mlbbId'] as String?,
      profileComplete: json['profileComplete'] as bool? ?? false,
      // The server always sends false; never infer it from anything else.
      mlbbIdVerified: json['mlbbIdVerified'] as bool? ?? false,
      createdAt: _parseDate(json['createdAt']),
      lastLoginAt: _parseDate(json['lastLoginAt']),
    );
  }

  static DateTime? _parseDate(Object? value) =>
      value is String ? DateTime.tryParse(value) : null;
}

/// What the server supports for sign-in, fetched at runtime so the app never
/// offers a button that cannot work.
class AuthConfig {
  const AuthConfig({
    required this.googleSignInEnabled,
    this.googleClientId,
    this.minPasswordLength = 8,
    this.maxPasswordLength = 128,
    this.usernamePattern = r'^[A-Za-z0-9_]{3,24}$',
    this.mlbbIdPattern = r'^\d{4,20}$',
  });

  final bool googleSignInEnabled;
  final String? googleClientId;
  final int minPasswordLength;
  final int maxPasswordLength;
  final String usernamePattern;
  final String mlbbIdPattern;

  factory AuthConfig.fromJson(Map<String, dynamic> json) {
    return AuthConfig(
      googleSignInEnabled: json['googleSignInEnabled'] as bool? ?? false,
      googleClientId: json['googleClientId'] as String?,
      minPasswordLength: (json['minPasswordLength'] as num?)?.toInt() ?? 8,
      maxPasswordLength: (json['maxPasswordLength'] as num?)?.toInt() ?? 128,
      usernamePattern: json['usernamePattern'] as String? ?? r'^[A-Za-z0-9_]{3,24}$',
      mlbbIdPattern: json['mlbbIdPattern'] as String? ?? r'^\d{4,20}$',
    );
  }
}

class AuthSessionResult {
  const AuthSessionResult({
    required this.sessionToken,
    required this.account,
    required this.isNewUser,
  });

  final String sessionToken;
  final Account account;
  final bool isNewUser;

  factory AuthSessionResult.fromJson(Map<String, dynamic> json) {
    return AuthSessionResult(
      sessionToken: json['sessionToken'] as String,
      account: Account.fromJson(json['user'] as Map<String, dynamic>),
      isNewUser: json['isNewUser'] as bool? ?? false,
    );
  }
}
