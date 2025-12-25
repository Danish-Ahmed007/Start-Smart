import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

/// Service for handling Firebase Authentication
class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Lazy initialization for GoogleSignIn to avoid crash if not configured
  GoogleSignIn? _googleSignIn;
  GoogleSignIn get googleSignIn {
    _googleSignIn ??= GoogleSignIn(scopes: ['email']);
    return _googleSignIn!;
  }

  // ============================================================
  // Auth State
  // ============================================================

  /// Stream of auth state changes
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  /// Current user (null if not logged in)
  User? get currentUser => _auth.currentUser;

  /// Check if user is logged in
  bool get isLoggedIn => currentUser != null;

  /// Check if user is anonymous
  bool get isAnonymous => currentUser?.isAnonymous ?? false;

  /// Get user display name or email
  String get userDisplayName {
    final user = currentUser;
    if (user == null) return 'Guest';
    if (user.isAnonymous) return 'Guest User';
    return user.displayName ?? user.email ?? 'User';
  }

  /// Get user email
  String? get userEmail => currentUser?.email;

  /// Get user photo URL
  String? get userPhotoUrl => currentUser?.photoURL;

  // ============================================================
  // Sign In Methods
  // ============================================================

  /// Sign in with Google
  Future<UserCredential?> signInWithGoogle() async {
    try {
      // Trigger the Google Sign-In flow
      final GoogleSignInAccount? googleUser = await googleSignIn.signIn();

      if (googleUser == null) {
        // User cancelled the sign-in
        return null;
      }

      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Create a new credential
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Sign in to Firebase with the credential
      final userCredential = await _auth.signInWithCredential(credential);

      // Create/update user document in Firestore
      await _createOrUpdateUser(userCredential.user);

      return userCredential;
    } catch (e) {
      print('Error signing in with Google: $e');
      rethrow;
    }
  }

  /// Sign in with Email and Password
  Future<UserCredential> signInWithEmail(String email, String password) async {
    try {
      final userCredential = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

      // Update last login
      await _updateLastLogin(userCredential.user);

      return userCredential;
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }

  /// Sign up with Email and Password
  Future<UserCredential> signUpWithEmail(String email, String password) async {
    try {
      final userCredential = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      // Create user document in Firestore
      await _createOrUpdateUser(userCredential.user);

      return userCredential;
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }

  /// Sign in anonymously (guest mode)
  Future<UserCredential> signInAnonymously() async {
    try {
      final userCredential = await _auth.signInAnonymously();

      // Create anonymous user document
      await _createOrUpdateUser(userCredential.user, isAnonymous: true);

      return userCredential;
    } catch (e) {
      print('Error signing in anonymously: $e');
      rethrow;
    }
  }

  // ============================================================
  // Sign Out
  // ============================================================

  /// Sign out the current user
  Future<void> signOut() async {
    try {
      // Sign out from Google if signed in with Google
      if (_googleSignIn != null && await _googleSignIn!.isSignedIn()) {
        await _googleSignIn!.signOut();
      }

      // Sign out from Firebase
      await _auth.signOut();
    } catch (e) {
      print('Error signing out: $e');
      rethrow;
    }
  }

  // ============================================================
  // Password Reset
  // ============================================================

  /// Send password reset email
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } on FirebaseAuthException catch (e) {
      throw _handleAuthException(e);
    }
  }

  // ============================================================
  // Firestore User Management
  // ============================================================

  /// Create or update user document in Firestore
  Future<void> _createOrUpdateUser(
    User? user, {
    bool isAnonymous = false,
  }) async {
    if (user == null) return;

    final userDoc = _firestore.collection('users').doc(user.uid);
    final docSnapshot = await userDoc.get();

    if (!docSnapshot.exists) {
      // Create new user document
      await userDoc.set({
        'uid': user.uid,
        'email': user.email,
        'displayName': user.displayName,
        'photoURL': user.photoURL,
        'isAnonymous': isAnonymous,
        'createdAt': FieldValue.serverTimestamp(),
        'lastLogin': FieldValue.serverTimestamp(),
        'totalSessions': 1,
        'provider': isAnonymous ? 'anonymous' : _getProvider(user),
      });
    } else {
      // Update existing user
      await userDoc.update({
        'lastLogin': FieldValue.serverTimestamp(),
        'totalSessions': FieldValue.increment(1),
      });
    }
  }

  /// Update last login timestamp
  Future<void> _updateLastLogin(User? user) async {
    if (user == null) return;

    await _firestore.collection('users').doc(user.uid).update({
      'lastLogin': FieldValue.serverTimestamp(),
      'totalSessions': FieldValue.increment(1),
    });
  }

  /// Get the auth provider used
  String _getProvider(User user) {
    if (user.providerData.isNotEmpty) {
      return user.providerData.first.providerId;
    }
    return 'unknown';
  }

  // ============================================================
  // Error Handling
  // ============================================================

  /// Convert Firebase auth exceptions to user-friendly messages
  String _handleAuthException(FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
        return 'No user found with this email.';
      case 'wrong-password':
        return 'Wrong password provided.';
      case 'email-already-in-use':
        return 'An account already exists with this email.';
      case 'invalid-email':
        return 'Please enter a valid email address.';
      case 'weak-password':
        return 'Password should be at least 6 characters.';
      case 'user-disabled':
        return 'This account has been disabled.';
      case 'too-many-requests':
        return 'Too many attempts. Please try again later.';
      case 'operation-not-allowed':
        return 'This sign-in method is not enabled.';
      default:
        return e.message ?? 'An error occurred. Please try again.';
    }
  }
}
