import 'package:flutter/material.dart';
import '../models/enhanced_recommendation.dart';
import '../services/api_service.dart';
import '../services/analytics_service.dart';

// Analytics service instance (private to this file)
final _analyticsService = AnalyticsService();

/// Enhanced analysis results screen with income data and area analysis
class EnhancedAnalysisResultsScreen extends StatefulWidget {
  final double latitude;
  final double longitude;
  final int radius;
  final String businessType;

  const EnhancedAnalysisResultsScreen({
    super.key,
    required this.latitude,
    required this.longitude,
    required this.radius,
    required this.businessType,
  });

  @override
  State<EnhancedAnalysisResultsScreen> createState() =>
      _EnhancedAnalysisResultsScreenState();
}

class _EnhancedAnalysisResultsScreenState
    extends State<EnhancedAnalysisResultsScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  bool _isLoading = true;
  EnhancedRecommendationFull? _recommendation;
  String? _error;

  // Animation controller
  late AnimationController _animationController;

  // Blue theme colors
  static const Color _primaryBlue = Color(0xFF1E40AF);
  static const Color _lightBlue = Color(0xFF3B82F6);
  static const Color _darkBlue = Color(0xFF1E3A8A);
  static const Color _accentBlue = Color(0xFF60A5FA);

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _analyticsService.trackScreenView(screenName: 'enhanced_analysis_results');
    _fetchRecommendation();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _apiService.dispose();
    super.dispose();
  }

  Future<void> _fetchRecommendation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Try enhanced endpoint first, fall back to debug endpoint if not available
      EnhancedRecommendationFull? recommendation;

      try {
        recommendation = await _apiService.getEnhancedRecommendation(
          lat: widget.latitude,
          lon: widget.longitude,
          radius: widget.radius,
        );
      } catch (e) {
        // Fall back to debug endpoint which has BEV data
        final debugData = await _apiService.getDebugRecommendation(
          lat: widget.latitude,
          lon: widget.longitude,
          radius: widget.radius,
        );
        recommendation = _convertDebugToEnhanced(debugData);
      }

      setState(() {
        _recommendation = recommendation;
        _isLoading = false;
      });
      _animationController.forward();

      // Track completion
      _analyticsService.trackAnalysisCompleted(
        businessType: widget.businessType,
        latitude: widget.latitude,
        longitude: widget.longitude,
        radius: widget.radius,
        mode: 'Enhanced',
        gymScore: recommendation!.gym.score,
        cafeScore: recommendation.cafe.score,
        recommendedType: recommendation.recommendation.bestCategory,
        processingTimeMs: recommendation.processingTimeMs,
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Determine area character based on top business categories
  String _determineAreaCharacter(List<(String, int)> catData, int total) {
    if (total == 0) return 'Undeveloped area';

    final topCat = catData.isNotEmpty ? catData[0].$1 : '';
    final topPct = catData.isNotEmpty && total > 0
        ? (catData[0].$2 / total * 100)
        : 0.0;

    final characterMap = {
      'Restaurants': 'Food & dining hub',
      'Cafes': 'Cafe culture area',
      'Gyms & Fitness': 'Health-conscious community',
      'Offices': 'Business district',
      'Schools': 'Education-focused neighborhood',
      'Banks': 'Financial services hub',
      'Healthcare': 'Healthcare corridor',
    };

    final character = characterMap[topCat] ?? 'Mixed-use area';

    if (topPct >= 40) {
      return '$character (strongly dominant)';
    } else if (topPct >= 25) {
      return '$character with diverse offerings';
    }
    return 'Diverse mixed-use area';
  }

  /// Generate backing factors from BEV data
  List<BackingFactor> _generateBackingFactors(
    int restaurantCount,
    int cafeCount,
    int gymCount,
    int officeCount,
    int schoolCount,
    int totalBusinesses,
    double avgRating,
  ) {
    final factors = <BackingFactor>[];
    final foodCount = restaurantCount + cafeCount;

    // Food density
    if (foodCount >= 8) {
      factors.add(
        BackingFactor(
          factor: 'High food establishment density',
          evidence:
              '$foodCount food businesses nearby ($restaurantCount restaurants, $cafeCount cafes)',
          implication: 'Indicates high foot traffic and food-seeking customers',
          strength: 'strong',
        ),
      );
    } else if (foodCount >= 4) {
      factors.add(
        BackingFactor(
          factor: 'Moderate food scene',
          evidence: '$foodCount food businesses in the area',
          implication: 'Room for differentiated food concepts',
          strength: 'moderate',
        ),
      );
    } else if (foodCount < 2) {
      factors.add(
        BackingFactor(
          factor: 'Food gap opportunity',
          evidence: 'Only $foodCount food businesses nearby',
          implication: 'Potential unserved demand for food options',
          strength: 'moderate',
        ),
      );
    }

    // Fitness competition
    if (gymCount >= 3) {
      factors.add(
        BackingFactor(
          factor: 'Competitive fitness market',
          evidence: '$gymCount fitness/wellness businesses',
          implication: 'High gym competition. Differentiation needed.',
          strength: 'strong',
        ),
      );
    } else if (gymCount == 0) {
      factors.add(
        BackingFactor(
          factor: 'Fitness gap',
          evidence: 'No gyms or fitness centers in the area',
          implication: 'Potential opportunity for fitness business',
          strength: 'moderate',
        ),
      );
    }

    // Office presence
    if (officeCount >= 5) {
      factors.add(
        BackingFactor(
          factor: 'Strong professional presence',
          evidence: '$officeCount offices/banks in area',
          implication:
              'Daytime working population needs lunch spots, cafes, quick services',
          strength: 'strong',
        ),
      );
    } else if (officeCount >= 2) {
      factors.add(
        BackingFactor(
          factor: 'Some professional activity',
          evidence: '$officeCount professional establishments nearby',
          implication: 'Good for services catering to professionals',
          strength: 'moderate',
        ),
      );
    }

    // Education
    if (schoolCount >= 3) {
      factors.add(
        BackingFactor(
          factor: 'Education hub',
          evidence: '$schoolCount educational institutions',
          implication:
              'Student population creates demand for affordable food and services',
          strength: 'strong',
        ),
      );
    }

    // Overall density
    if (totalBusinesses >= 30) {
      factors.add(
        BackingFactor(
          factor: 'High business density zone',
          evidence: '$totalBusinesses total businesses in search radius',
          implication: 'Established commercial area with proven foot traffic',
          strength: 'strong',
        ),
      );
    } else if (totalBusinesses <= 10) {
      factors.add(
        BackingFactor(
          factor: 'Low business density',
          evidence: 'Only $totalBusinesses businesses in the area',
          implication:
              'May be emerging area. Lower competition but unproven demand.',
          strength: 'weak',
        ),
      );
    }

    // Quality indicator
    if (avgRating >= 4.2) {
      factors.add(
        BackingFactor(
          factor: 'High quality area',
          evidence:
              'Average business rating: ${avgRating.toStringAsFixed(1)}/5.0',
          implication:
              'Customers expect quality. Premium positioning may work.',
          strength: 'moderate',
        ),
      );
    }

    return factors;
  }

  /// Convert debug endpoint response to EnhancedRecommendationFull
  EnhancedRecommendationFull _convertDebugToEnhanced(
    Map<String, dynamic> debug,
  ) {
    final bev = debug['bev'] as Map<String, dynamic>? ?? {};
    final recommendation =
        debug['recommendation'] as Map<String, dynamic>? ?? {};
    final timing = debug['timing'] as Map<String, dynamic>? ?? {};
    final location = debug['location'] as Map<String, dynamic>? ?? {};

    // Extract BEV counts
    final restaurantCount = bev['restaurant_count'] as int? ?? 0;
    final cafeCount = bev['cafe_count'] as int? ?? 0;
    final gymCount = bev['gym_count'] as int? ?? 0;
    final officeCount = bev['office_count'] as int? ?? 0;
    final schoolCount = bev['school_count'] as int? ?? 0;
    final bankCount = bev['bank_count'] as int? ?? 0;
    final healthcareCount = bev['healthcare_count'] as int? ?? 0;
    final incomeProxy = bev['income_proxy'] as String? ?? 'mid';

    // Build categories from BEV data
    final catData = [
      ('Restaurants', restaurantCount),
      ('Cafes', cafeCount),
      ('Gyms & Fitness', gymCount),
      ('Offices', officeCount),
      ('Schools', schoolCount),
      ('Banks', bankCount),
      ('Healthcare', healthcareCount),
    ];

    catData.sort((a, b) => b.$2.compareTo(a.$2));
    final totalBusinesses = catData.fold(0, (sum, item) => sum + item.$2);
    final total = totalBusinesses > 0 ? totalBusinesses : 1;

    final categories = <CategoryCount>[];
    for (var i = 0; i < catData.length && i < 5; i++) {
      if (catData[i].$2 > 0) {
        categories.add(
          CategoryCount(
            category: catData[i].$1,
            count: catData[i].$2,
            percentage: (catData[i].$2 / total * 100),
          ),
        );
      }
    }

    // Income data based on income proxy
    final incomeValues = {
      'high': (450000, 380000, 'upper-middle', 'high', 0.85, 800, 2500, 12000),
      'mid': (350000, 300000, 'middle', 'moderate', 0.70, 600, 1800, 8000),
      'low': (200000, 180000, 'lower-middle', 'low', 0.50, 400, 1200, 5000),
    };
    final inc = incomeValues[incomeProxy] ?? incomeValues['mid']!;

    // Get scores
    final gymScore = (debug['final_scores']?['gym'] as num?)?.toDouble() ?? 0.5;
    final cafeScore =
        (debug['final_scores']?['cafe'] as num?)?.toDouble() ?? 0.5;
    final bestCategory = recommendation['best_category'] as String? ?? 'cafe';
    final bestScore = (recommendation['score'] as num?)?.toDouble() ?? 0.5;
    final suitability = recommendation['suitability'] as String? ?? 'moderate';
    final message =
        recommendation['message'] as String? ?? 'Analysis complete.';

    // Build supporting factors
    final gymPositive = <SupportingFactor>[];
    final gymNegative = <SupportingFactor>[];
    final cafePositive = <SupportingFactor>[];
    final cafeNegative = <SupportingFactor>[];

    if (officeCount > 0) {
      gymPositive.add(
        SupportingFactor(
          factor: '$officeCount offices nearby',
          count: officeCount,
          impact: 'positive',
          reason: 'Office workers often seek fitness facilities',
        ),
      );
      cafePositive.add(
        SupportingFactor(
          factor: '$officeCount offices nearby',
          count: officeCount,
          impact: 'positive',
          reason: 'Office workers are regular coffee consumers',
        ),
      );
    }

    if (restaurantCount > 0) {
      cafePositive.add(
        SupportingFactor(
          factor: '$restaurantCount restaurants nearby',
          count: restaurantCount,
          impact: 'positive',
          reason: 'Food-friendly area with foot traffic',
        ),
      );
    }

    if (gymCount > 2) {
      gymNegative.add(
        SupportingFactor(
          factor: '$gymCount existing gyms',
          count: gymCount,
          impact: 'negative',
          reason: 'High competition in the area',
        ),
      );
    }

    if (cafeCount > 3) {
      cafeNegative.add(
        SupportingFactor(
          factor: '$cafeCount existing cafes',
          count: cafeCount,
          impact: 'negative',
          reason: 'Market may be saturated',
        ),
      );
    }

    if (schoolCount > 0) {
      gymPositive.add(
        SupportingFactor(
          factor: '$schoolCount schools nearby',
          count: schoolCount,
          impact: 'positive',
          reason: 'Students and faculty are fitness-conscious',
        ),
      );
    }

    return EnhancedRecommendationFull(
      gridId: debug['grid_id'] as String? ?? 'custom',
      location: {
        'lat': (location['lat'] as num?)?.toDouble() ?? 0.0,
        'lon': (location['lon'] as num?)?.toDouble() ?? 0.0,
        'radius': (location['radius'] as num?)?.toDouble() ?? 200.0,
      },
      areaAnalysis: AreaAnalysis(
        totalBusinesses: totalBusinesses,
        top5Categories: categories,
        areaCharacter: _determineAreaCharacter(catData, totalBusinesses),
        backingFactors: _generateBackingFactors(
          restaurantCount,
          cafeCount,
          gymCount,
          officeCount,
          schoolCount,
          totalBusinesses,
          bev['avg_rating'] as double? ?? 0.0,
        ),
      ),
      incomeData: IncomeData(
        avgHouseholdIncome: inc.$1,
        medianIncome: inc.$2,
        incomeBracket: inc.$3,
        spendingPower: inc.$4,
        affordabilityScore: inc.$5,
        keyDemographics: ['Local Residents', 'Professionals'],
        consumerBehavior: ConsumerBehavior(
          avgMealSpending: inc.$7,
          avgCoffeeSpending: inc.$6,
          gymBudgetMonthly: inc.$8,
          priceSensitivity: incomeProxy == 'high' ? 'low' : 'moderate',
        ),
      ),
      recommendation: EnhancedRecommendationOutput(
        bestCategory: bestCategory,
        confidenceScore: bestScore,
        suitability: suitability,
        summary: message,
        keyNumbers: {
          'restaurants_nearby': restaurantCount,
          'cafes_nearby': cafeCount,
          'gyms_nearby': gymCount,
          'offices_nearby': officeCount,
          'total_businesses': totalBusinesses,
        },
      ),
      supportingFactors: {
        'for_gym': gymPositive,
        'against_gym': gymNegative,
        'for_cafe': cafePositive,
        'against_cafe': cafeNegative,
      },
      gym: CategoryScore(
        score: gymScore,
        suitability: gymScore >= 0.65
            ? 'good'
            : gymScore >= 0.5
            ? 'moderate'
            : 'poor',
        reasoning: 'Based on area analysis',
        positiveFactors: gymPositive.map((f) => f.factor).toList(),
        concerns: gymNegative.map((f) => f.factor).toList(),
      ),
      cafe: CategoryScore(
        score: cafeScore,
        suitability: cafeScore >= 0.65
            ? 'good'
            : cafeScore >= 0.5
            ? 'moderate'
            : 'poor',
        reasoning: 'Based on area analysis',
        positiveFactors: cafePositive.map((f) => f.factor).toList(),
        concerns: cafeNegative.map((f) => f.factor).toList(),
      ),
      processingTimeMs: (timing['total_ms'] as num?)?.round() ?? 0,
      totalBusinesses: totalBusinesses,
      modelUsed: debug['mode'] as String? ?? 'rule-based',
    );
  }

  /// Convert legacy EnhancedRecommendation to EnhancedRecommendationFull
  EnhancedRecommendationFull _convertLegacyToEnhanced(
    EnhancedRecommendation legacy,
  ) {
    // Create synthetic area analysis from BEV data
    final bev = legacy.bev;
    final categories = <CategoryCount>[];

    if (bev != null) {
      final catData = [
        ('restaurants', bev.restaurantCount),
        ('cafes', bev.cafeCount),
        ('gyms_fitness', bev.gymCount),
        ('offices_corporate', bev.officeCount),
        ('schools', bev.schoolCount),
        ('banks_finance', bev.bankCount),
        ('healthcare', bev.healthcareCount),
      ];

      catData.sort((a, b) => b.$2.compareTo(a.$2));
      final total = bev.totalBusinesses > 0 ? bev.totalBusinesses : 1;

      for (var i = 0; i < catData.length && i < 5; i++) {
        if (catData[i].$2 > 0) {
          categories.add(
            CategoryCount(
              category: catData[i].$1,
              count: catData[i].$2,
              percentage: (catData[i].$2 / total * 100),
            ),
          );
        }
      }
    }

    // Create synthetic income data based on income proxy
    final incomeProxy = bev?.incomeProxy ?? 'mid';
    final incomeValues = {
      'high': (450000, 380000, 'upper-middle', 'high', 0.85, 800, 2500, 12000),
      'mid': (350000, 300000, 'middle', 'moderate', 0.70, 600, 1800, 8000),
      'low': (200000, 180000, 'lower-middle', 'low', 0.50, 400, 1200, 5000),
    };
    final inc = incomeValues[incomeProxy] ?? incomeValues['mid']!;

    return EnhancedRecommendationFull(
      gridId: legacy.gridId,
      location: {
        'lat': legacy.lat,
        'lon': legacy.lon,
        'radius': legacy.radius.toDouble(),
      },
      areaAnalysis: AreaAnalysis(
        totalBusinesses: bev?.totalBusinesses ?? 0,
        top5Categories: categories,
      ),
      incomeData: IncomeData(
        avgHouseholdIncome: inc.$1,
        medianIncome: inc.$2,
        incomeBracket: inc.$3,
        spendingPower: inc.$4,
        affordabilityScore: inc.$5,
        keyDemographics: ['Local Residents', 'Professionals'],
        consumerBehavior: ConsumerBehavior(
          avgMealSpending: inc.$7,
          avgCoffeeSpending: inc.$6,
          gymBudgetMonthly: inc.$8,
          priceSensitivity: incomeProxy == 'high' ? 'low' : 'moderate',
        ),
      ),
      recommendation: EnhancedRecommendationOutput(
        bestCategory: legacy.recommendation.bestCategory,
        confidenceScore: legacy.recommendation.score,
        suitability: legacy.recommendation.suitability,
        summary: legacy.recommendation.message,
        keyNumbers: {
          'restaurants_nearby': bev?.restaurantCount ?? 0,
          'cafes_nearby': bev?.cafeCount ?? 0,
          'gyms_nearby': bev?.gymCount ?? 0,
          'offices_nearby': bev?.officeCount ?? 0,
          'total_businesses': bev?.totalBusinesses ?? 0,
        },
      ),
      supportingFactors: {
        'for_${legacy.recommendation.bestCategory}': legacy
            .winningScore
            .positiveFactors
            .map(
              (f) => SupportingFactor(
                factor: f,
                count: 1,
                impact: 'positive',
                reason: f,
              ),
            )
            .toList(),
        'against_${legacy.recommendation.bestCategory}': legacy
            .winningScore
            .concerns
            .map(
              (f) => SupportingFactor(
                factor: f,
                count: 1,
                impact: 'negative',
                reason: f,
              ),
            )
            .toList(),
      },
      gym: legacy.gym,
      cafe: legacy.cafe,
      processingTimeMs: legacy.processingTimeMs,
      totalBusinesses: bev?.totalBusinesses ?? 0,
      modelUsed: legacy.isLLMPowered ? 'llama-3.3-70b' : 'rule-based',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [_primaryBlue, _darkBlue],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildAppBar(),
              Expanded(child: _buildBody()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Location Analysis',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Radius: ${widget.radius}m',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.8),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return _buildLoadingState();
    }
    if (_error != null) {
      return _buildErrorState();
    }
    if (_recommendation == null) {
      return _buildEmptyState();
    }
    return _buildContent();
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(color: Colors.white),
          const SizedBox(height: 20),
          Text(
            'Analyzing location...',
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Gathering business data and income information',
            style: TextStyle(
              color: Colors.white.withOpacity(0.6),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.white, size: 48),
          const SizedBox(height: 16),
          Text(
            'Analysis Failed',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Text(
              _error ?? 'Unknown error',
              style: TextStyle(color: Colors.white.withOpacity(0.8)),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _fetchRecommendation,
            child: const Text('Try Again'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Text('No data available', style: TextStyle(color: Colors.white)),
    );
  }

  Widget _buildContent() {
    final rec = _recommendation!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Main recommendation card
          _buildRecommendationCard(rec),
          const SizedBox(height: 16),

          // Top 5 business categories
          _buildCategoriesCard(rec),
          const SizedBox(height: 16),

          // Data-backed insights (from area analysis)
          if (rec.areaAnalysis.backingFactors.isNotEmpty)
            _buildBackingInsightsCard(rec),
          if (rec.areaAnalysis.backingFactors.isNotEmpty)
            const SizedBox(height: 16),

          // Income data card
          _buildIncomeCard(rec),
          const SizedBox(height: 16),

          // Supporting factors
          _buildFactorsCard(rec),
          const SizedBox(height: 16),

          // Score comparison
          _buildScoreComparisonCard(rec),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildRecommendationCard(EnhancedRecommendationFull rec) {
    final isGym = rec.recommendation.bestCategory == 'gym';
    final color = _getSuitabilityColor(rec.recommendation.suitability);

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isGym ? Icons.fitness_center : Icons.coffee,
                  color: color,
                  size: 32,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Best for: ${isGym ? "GYM" : "CAFE"}',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: _primaryBlue,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '${rec.recommendation.scorePercent}% Confidence • ${rec.recommendation.suitability.toUpperCase()}',
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Divider(),
          const SizedBox(height: 12),
          Text(
            rec.recommendation.summary,
            style: TextStyle(
              fontSize: 15,
              color: Colors.grey[700],
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoriesCard(EnhancedRecommendationFull rec) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.business, color: _primaryBlue),
              const SizedBox(width: 8),
              const Text(
                'Top Business Categories',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: _accentBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${rec.areaAnalysis.totalBusinesses} total',
                  style: TextStyle(
                    color: _primaryBlue,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...rec.areaAnalysis.top5Categories.asMap().entries.map((entry) {
            final index = entry.key;
            final cat = entry.value;
            return _buildCategoryRow(cat, index + 1);
          }),
        ],
      ),
    );
  }

  Widget _buildCategoryRow(CategoryCount cat, int rank) {
    final colors = [
      const Color(0xFF3B82F6),
      const Color(0xFF10B981),
      const Color(0xFFF59E0B),
      const Color(0xFF8B5CF6),
      const Color(0xFFEC4899),
    ];
    final color = colors[(rank - 1) % colors.length];

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                alignment: Alignment.center,
                child: Text(
                  '#$rank',
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      cat.displayName,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: cat.percentage / 100,
                        backgroundColor: Colors.grey[200],
                        valueColor: AlwaysStoppedAnimation<Color>(color),
                        minHeight: 6,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${cat.count}',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: color,
                    ),
                  ),
                  Text(
                    '${cat.percentage.toStringAsFixed(1)}%',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
          // Show sample business names if available
          if (cat.businessNames.isNotEmpty) ...[
            const SizedBox(height: 6),
            Padding(
              padding: const EdgeInsets.only(left: 40),
              child: Text(
                'e.g., ${cat.businessNames.take(3).join(', ')}',
                style: TextStyle(
                  color: Colors.grey[500],
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildIncomeCard(EnhancedRecommendationFull rec) {
    final income = rec.incomeData;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.account_balance_wallet, color: _primaryBlue),
              const SizedBox(width: 8),
              const Text(
                'Income & Demographics',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Main income stat
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  _primaryBlue.withOpacity(0.1),
                  _accentBlue.withOpacity(0.05),
                ],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                Text(
                  income.formattedIncome,
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: _primaryBlue,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Average Household Income',
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Income details
          Row(
            children: [
              Expanded(
                child: _buildIncomeMetric(
                  'Income Bracket',
                  income.incomeBracket.replaceAll('-', '\n'),
                  Icons.trending_up,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildIncomeMetric(
                  'Spending Power',
                  income.spendingPower,
                  Icons.shopping_bag,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Demographics
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: income.keyDemographics.map((demo) {
              return Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  demo,
                  style: TextStyle(color: Colors.grey[700], fontSize: 13),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),

          // Consumer behavior
          const Divider(),
          const SizedBox(height: 12),
          Text(
            'Consumer Spending',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildSpendingChip(
                  '☕ Coffee',
                  'PKR ${income.consumerBehavior.avgCoffeeSpending}',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildSpendingChip(
                  '🍽️ Meal',
                  'PKR ${income.consumerBehavior.avgMealSpending}',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildSpendingChip(
                  '🏋️ Gym/mo',
                  'PKR ${income.consumerBehavior.gymBudgetMonthly}',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildIncomeMetric(String label, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        children: [
          Icon(icon, color: _lightBlue, size: 20),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildSpendingChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
      decoration: BoxDecoration(
        color: _accentBlue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[700])),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 12,
              color: _primaryBlue,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFactorsCard(EnhancedRecommendationFull rec) {
    final positiveFactors = rec.winningPositiveFactors;
    final negativeFactors = rec.winningNegativeFactors;
    final categoryName = rec.recommendation.bestCategory.toUpperCase();

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.analytics, color: _primaryBlue),
              const SizedBox(width: 8),
              Text(
                'Supporting Factors for $categoryName',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (positiveFactors.isNotEmpty) ...[
            _buildFactorSection('Positive Factors', positiveFactors, true),
            const SizedBox(height: 16),
          ],

          if (negativeFactors.isNotEmpty) ...[
            _buildFactorSection('Concerns', negativeFactors, false),
          ],

          if (positiveFactors.isEmpty && negativeFactors.isEmpty)
            Text(
              'No specific factors identified',
              style: TextStyle(color: Colors.grey[600]),
            ),
        ],
      ),
    );
  }

  Widget _buildFactorSection(
    String title,
    List<SupportingFactor> factors,
    bool isPositive,
  ) {
    final color = isPositive
        ? const Color(0xFF10B981)
        : const Color(0xFFF59E0B);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              isPositive ? Icons.thumb_up : Icons.warning_amber,
              color: color,
              size: 18,
            ),
            const SizedBox(width: 6),
            Text(
              title,
              style: TextStyle(fontWeight: FontWeight.w600, color: color),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...factors.map((factor) => _buildFactorItem(factor, color)),
      ],
    );
  }

  Widget _buildFactorItem(SupportingFactor factor, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  factor.factor,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: color.withOpacity(0.9),
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            factor.reason,
            style: TextStyle(color: Colors.grey[700], fontSize: 13),
          ),
        ],
      ),
    );
  }

  /// Build the data-backed insights card from area analysis
  Widget _buildBackingInsightsCard(EnhancedRecommendationFull rec) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb, color: _primaryBlue),
              const SizedBox(width: 8),
              const Text(
                'Data-Backed Insights',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          if (rec.areaAnalysis.areaCharacter.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _accentBlue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  Icon(Icons.location_city, color: _primaryBlue, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Area Type: ${rec.areaAnalysis.areaCharacter}',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: _primaryBlue,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          ...rec.areaAnalysis.backingFactors.map(
            (factor) => _buildBackingFactorItem(factor),
          ),
        ],
      ),
    );
  }

  /// Build a single backing factor item
  Widget _buildBackingFactorItem(BackingFactor factor) {
    final color = factor.isStrong
        ? const Color(0xFF10B981)
        : factor.isModerate
        ? const Color(0xFF3B82F6)
        : const Color(0xFFF59E0B);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  factor.strength.toUpperCase(),
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  factor.factor,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.data_usage, size: 14, color: Colors.grey[600]),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  factor.evidence,
                  style: TextStyle(
                    color: Colors.grey[700],
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.arrow_forward, size: 14, color: color),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  factor.implication,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildScoreComparisonCard(EnhancedRecommendationFull rec) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.compare, color: _primaryBlue),
              const SizedBox(width: 8),
              const Text(
                'Score Comparison',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildScoreBox(
                  'GYM',
                  rec.gym.score,
                  rec.gym.suitability,
                  Icons.fitness_center,
                  rec.recommendation.bestCategory == 'gym',
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildScoreBox(
                  'CAFE',
                  rec.cafe.score,
                  rec.cafe.suitability,
                  Icons.coffee,
                  rec.recommendation.bestCategory == 'cafe',
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.timer, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 6),
                Text(
                  'Analysis completed in ${rec.processingTimeMs}ms',
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreBox(
    String label,
    double score,
    String suitability,
    IconData icon,
    bool isWinner,
  ) {
    final color = _getSuitabilityColor(suitability);
    final percent = (score * 100).round();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isWinner ? color.withOpacity(0.1) : Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isWinner ? color : Colors.grey[200]!,
          width: isWinner ? 2 : 1,
        ),
      ),
      child: Column(
        children: [
          if (isWinner)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                '✓ BEST',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          Icon(icon, size: 32, color: isWinner ? color : Colors.grey[400]),
          const SizedBox(height: 8),
          Text(
            label,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: isWinner ? color : Colors.grey[600],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$percent%',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: isWinner ? color : Colors.grey[500],
            ),
          ),
          Text(
            suitability,
            style: TextStyle(
              fontSize: 12,
              color: isWinner ? color : Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Color _getSuitabilityColor(String suitability) {
    switch (suitability.toLowerCase()) {
      case 'excellent':
        return const Color(0xFF10B981);
      case 'good':
        return const Color(0xFF3B82F6);
      case 'moderate':
        return const Color(0xFFF59E0B);
      case 'poor':
        return const Color(0xFFEF4444);
      default:
        return Colors.grey[600]!;
    }
  }
}
