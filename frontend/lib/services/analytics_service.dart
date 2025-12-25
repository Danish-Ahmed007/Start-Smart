import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

/// Service for tracking user analytics events to Firestore
///
/// This service tracks all user interactions with the app to provide
/// auditable metrics for the BML cycle assignment.
class AnalyticsService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // Session tracking
  String? _currentSessionId;
  DateTime? _sessionStartTime;

  // ============================================================
  // Session Management
  // ============================================================

  /// Start a new session when user opens the app
  Future<String> startSession() async {
    _sessionStartTime = DateTime.now();

    final sessionDoc = await _firestore.collection('sessions').add({
      'userId': _auth.currentUser?.uid ?? 'anonymous',
      'userEmail': _auth.currentUser?.email,
      'isAnonymous': _auth.currentUser?.isAnonymous ?? true,
      'startTime': FieldValue.serverTimestamp(),
      'endTime': null,
      'duration': null,
      'eventsCount': 0,
      'analysesStarted': 0,
      'analysesCompleted': 0,
      'feedbackGiven': 0,
    });

    _currentSessionId = sessionDoc.id;
    return sessionDoc.id;
  }

  /// End the current session
  Future<void> endSession() async {
    if (_currentSessionId == null || _sessionStartTime == null) return;

    final duration = DateTime.now().difference(_sessionStartTime!);

    await _firestore.collection('sessions').doc(_currentSessionId).update({
      'endTime': FieldValue.serverTimestamp(),
      'durationSeconds': duration.inSeconds,
    });

    _currentSessionId = null;
    _sessionStartTime = null;
  }

  // ============================================================
  // Generic Event Tracking
  // ============================================================

  /// Track any custom event
  Future<void> trackEvent({
    required String eventType,
    Map<String, dynamic>? data,
  }) async {
    try {
      await _firestore.collection('analytics_events').add({
        'userId': _auth.currentUser?.uid ?? 'anonymous',
        'userEmail': _auth.currentUser?.email,
        'isAnonymous': _auth.currentUser?.isAnonymous ?? true,
        'sessionId': _currentSessionId,
        'eventType': eventType,
        'timestamp': FieldValue.serverTimestamp(),
        'data': data ?? {},
      });

      // Update session event count
      if (_currentSessionId != null) {
        await _firestore.collection('sessions').doc(_currentSessionId).update({
          'eventsCount': FieldValue.increment(1),
        });
      }
    } catch (e) {
      print('Error tracking event: $e');
      // Don't throw - analytics shouldn't break the app
    }
  }

  // ============================================================
  // Specific Event Tracking Methods
  // ============================================================

  /// Track when user starts an analysis
  Future<void> trackAnalysisStarted({
    required String businessType,
    required String mode,
    required int radius,
    required double latitude,
    required double longitude,
  }) async {
    await trackEvent(
      eventType: 'analysis_started',
      data: {
        'businessType': businessType,
        'mode': mode,
        'radius': radius,
        'latitude': latitude,
        'longitude': longitude,
      },
    );

    // Update session counter
    if (_currentSessionId != null) {
      await _firestore.collection('sessions').doc(_currentSessionId).update({
        'analysesStarted': FieldValue.increment(1),
      });
    }
  }

  /// Track when analysis completes successfully
  Future<void> trackAnalysisCompleted({
    required String businessType,
    required String mode,
    required int radius,
    required double latitude,
    required double longitude,
    required double gymScore,
    required double cafeScore,
    required String recommendedType,
    required int processingTimeMs,
  }) async {
    await trackEvent(
      eventType: 'analysis_completed',
      data: {
        'businessType': businessType,
        'mode': mode,
        'radius': radius,
        'latitude': latitude,
        'longitude': longitude,
        'gymScore': gymScore,
        'cafeScore': cafeScore,
        'recommendedType': recommendedType,
        'processingTimeMs': processingTimeMs,
      },
    );

    // Update session counter
    if (_currentSessionId != null) {
      await _firestore.collection('sessions').doc(_currentSessionId).update({
        'analysesCompleted': FieldValue.increment(1),
      });
    }
  }

  /// Track when user gives feedback (thumbs up/down)
  Future<void> trackFeedback({
    required String businessType,
    required String feedback, // 'positive' or 'negative'
    required double latitude,
    required double longitude,
    required double score,
    String? comment,
  }) async {
    await trackEvent(
      eventType: 'feedback_given',
      data: {
        'businessType': businessType,
        'feedback': feedback,
        'latitude': latitude,
        'longitude': longitude,
        'score': score,
        'comment': comment,
      },
    );

    // Update session counter
    if (_currentSessionId != null) {
      await _firestore.collection('sessions').doc(_currentSessionId).update({
        'feedbackGiven': FieldValue.increment(1),
      });
    }

    // Also store in dedicated feedback collection for easy querying
    await _firestore.collection('user_feedback').add({
      'userId': _auth.currentUser?.uid ?? 'anonymous',
      'sessionId': _currentSessionId,
      'businessType': businessType,
      'feedback': feedback,
      'latitude': latitude,
      'longitude': longitude,
      'score': score,
      'comment': comment,
      'timestamp': FieldValue.serverTimestamp(),
    });
  }

  /// Track mode selection (Fast vs AI)
  Future<void> trackModeSelection({required String mode}) async {
    await trackEvent(eventType: 'mode_selected', data: {'mode': mode});
  }

  /// Track business type selection
  Future<void> trackBusinessTypeSelection({
    required String businessType,
  }) async {
    await trackEvent(
      eventType: 'business_type_selected',
      data: {'businessType': businessType},
    );
  }

  /// Track radius selection
  Future<void> trackRadiusSelection({required int radius}) async {
    await trackEvent(eventType: 'radius_selected', data: {'radius': radius});
  }

  /// Track location selection on map
  Future<void> trackLocationSelection({
    required double latitude,
    required double longitude,
  }) async {
    await trackEvent(
      eventType: 'location_selected',
      data: {'latitude': latitude, 'longitude': longitude},
    );
  }

  /// Track screen view
  Future<void> trackScreenView({required String screenName}) async {
    await trackEvent(
      eventType: 'screen_view',
      data: {'screenName': screenName},
    );
  }

  /// Track user login
  Future<void> trackLogin({
    required String method, // 'google', 'email', 'anonymous'
  }) async {
    await trackEvent(eventType: 'user_login', data: {'method': method});
  }

  /// Track user signup
  Future<void> trackSignup({required String method}) async {
    await trackEvent(eventType: 'user_signup', data: {'method': method});
  }

  /// Track user logout
  Future<void> trackLogout() async {
    await trackEvent(eventType: 'user_logout', data: {});
  }

  /// Track analysis error
  Future<void> trackAnalysisError({
    required String businessType,
    required String mode,
    required String error,
  }) async {
    await trackEvent(
      eventType: 'analysis_error',
      data: {'businessType': businessType, 'mode': mode, 'error': error},
    );
  }

  // ============================================================
  // Metrics Queries (for dashboard/export)
  // ============================================================

  /// Get total number of analyses completed
  Future<int> getTotalAnalysesCompleted() async {
    final snapshot = await _firestore
        .collection('analytics_events')
        .where('eventType', isEqualTo: 'analysis_completed')
        .count()
        .get();
    return snapshot.count ?? 0;
  }

  /// Get total number of analyses started
  Future<int> getTotalAnalysesStarted() async {
    final snapshot = await _firestore
        .collection('analytics_events')
        .where('eventType', isEqualTo: 'analysis_started')
        .count()
        .get();
    return snapshot.count ?? 0;
  }

  /// Get total feedback count
  Future<int> getTotalFeedbackCount() async {
    final snapshot = await _firestore.collection('user_feedback').count().get();
    return snapshot.count ?? 0;
  }

  /// Get positive feedback count
  Future<int> getPositiveFeedbackCount() async {
    final snapshot = await _firestore
        .collection('user_feedback')
        .where('feedback', isEqualTo: 'positive')
        .count()
        .get();
    return snapshot.count ?? 0;
  }

  /// Get AI mode usage count
  Future<int> getAIModeUsageCount() async {
    final snapshot = await _firestore
        .collection('analytics_events')
        .where('eventType', isEqualTo: 'analysis_completed')
        .where('data.mode', isEqualTo: 'AI')
        .count()
        .get();
    return snapshot.count ?? 0;
  }
}

// Global instance for easy access
final analyticsService = AnalyticsService();
