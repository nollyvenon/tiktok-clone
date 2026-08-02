class User {
  final String id;
  // Null when parsed from a UserPublicProfile (follower/following lists,
  // video author) - the backend only includes email on the owner's own
  // full profile responses.
  final String? email;
  final String username;
  final String? firstName;
  final String? lastName;
  final String? bio;
  final String? avatarUrl;
  final String? coverUrl;
  final String? website;
  final bool isCreator;
  final bool isVerified;
  // Only populated on followers/following list entries (mutual-follow
  // context relative to the requesting user); absent elsewhere.
  final bool isFollowing;
  final bool isFollowedBy;

  User({
    required this.id,
    required this.email,
    required this.username,
    this.firstName,
    this.lastName,
    this.bio,
    this.avatarUrl,
    this.coverUrl,
    this.website,
    required this.isCreator,
    required this.isVerified,
    this.isFollowing = false,
    this.isFollowedBy = false,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String?,
      username: json['username'] as String,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      bio: json['bio'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      coverUrl: json['cover_url'] as String?,
      website: json['website'] as String?,
      isCreator: json['is_creator'] as bool? ?? false,
      isVerified: json['is_verified'] as bool? ?? false,
      isFollowing: json['is_following'] as bool? ?? false,
      isFollowedBy: json['is_followed_by'] as bool? ?? false,
    );
  }

  String get displayName {
    final name = [firstName, lastName].where((s) => s != null && s.isNotEmpty).join(' ');
    return name.isNotEmpty ? name : username;
  }
}
