// Enhanced recommendation models for the LLM-powered recommendation engine
// Supports both fast (rule-only) and full (rule + LLM) modes

/// Category-specific score with reasoning
class CategoryScore {
  final double score;
  final String suitability;
  final String? reasoning;
  final List<String> positiveFactors;
  final List<String> concerns;
  final List<RuleTriggered>? rulesTriggered;

  CategoryScore({
    required this.score,
    required this.suitability,
    this.reasoning,
    this.positiveFactors = const [],
    this.concerns = const [],
    this.rulesTriggered,
  });

  /// Score as percentage (0-100)
  int get scorePercent => (score * 100).round();

  /// Check if this is a recommended location
  bool get isRecommended => score >= 0.45;

  /// Get color-coded suitability
  String get suitabilityEmoji {
    switch (suitability) {
      case 'excellent':
        return '🌟';
      case 'good':
        return '✅';
      case 'moderate':
        return '⚠️';
      case 'poor':
        return '❌';
      case 'not_recommended':
        return '🚫';
      default:
        return '❓';
    }
  }

  factory CategoryScore.fromJson(Map<String, dynamic> json) {
    return CategoryScore(
      score: (json['score'] as num).toDouble(),
      suitability: json['suitability'] as String? ?? 'moderate',
      reasoning: json['reasoning'] as String?,
      positiveFactors:
          (json['positive_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      concerns:
          (json['concerns'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      rulesTriggered: (json['rules_triggered'] as List<dynamic>?)
          ?.map((e) => RuleTriggered.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'score': score,
    'suitability': suitability,
    'reasoning': reasoning,
    'positive_factors': positiveFactors,
    'concerns': concerns,
  };
}

/// Rule that was triggered during evaluation
class RuleTriggered {
  final String rule;
  final String delta;
  final String? reason;

  RuleTriggered({required this.rule, required this.delta, this.reason});

  bool get isPositive => delta.startsWith('+');

  factory RuleTriggered.fromJson(Map<String, dynamic> json) {
    return RuleTriggered(
      rule: json['rule'] as String,
      delta: json['delta'] as String,
      reason: json['reason'] as String?,
    );
  }
}

/// Overall recommendation summary
class RecommendationSummary {
  final String bestCategory;
  final double score;
  final String suitability;
  final String message;

  RecommendationSummary({
    required this.bestCategory,
    required this.score,
    required this.suitability,
    required this.message,
  });

  factory RecommendationSummary.fromJson(Map<String, dynamic> json) {
    return RecommendationSummary(
      bestCategory: json['best_category'] as String,
      score: (json['score'] as num).toDouble(),
      suitability: json['suitability'] as String,
      message: json['message'] as String,
    );
  }
}

/// LLM-specific insights
class LLMInsights {
  final List<String> keyFactors;
  final List<String> risks;
  final String recommendation;

  LLMInsights({
    required this.keyFactors,
    required this.risks,
    required this.recommendation,
  });

  factory LLMInsights.fromJson(Map<String, dynamic> json) {
    return LLMInsights(
      keyFactors:
          (json['key_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      risks:
          (json['risks'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      recommendation: json['recommendation'] as String? ?? '',
    );
  }
}

/// Business Environment Vector summary - shows nearby businesses in the area
class BEVSummary {
  final int restaurantCount;
  final int cafeCount;
  final int gymCount;
  final int officeCount;
  final int schoolCount;
  final int bankCount;
  final int transitCount;
  final int mallCount;
  final int parkCount;
  final int healthcareCount;
  final int totalBusinesses;
  final double avgRating;
  final String? incomeProxy;

  BEVSummary({
    this.restaurantCount = 0,
    this.cafeCount = 0,
    this.gymCount = 0,
    this.officeCount = 0,
    this.schoolCount = 0,
    this.bankCount = 0,
    this.transitCount = 0,
    this.mallCount = 0,
    this.parkCount = 0,
    this.healthcareCount = 0,
    this.totalBusinesses = 0,
    this.avgRating = 0.0,
    this.incomeProxy,
  });

  factory BEVSummary.fromJson(Map<String, dynamic> json) {
    return BEVSummary(
      restaurantCount: json['restaurant_count'] as int? ?? 0,
      cafeCount: json['cafe_count'] as int? ?? 0,
      gymCount: json['gym_count'] as int? ?? 0,
      officeCount: json['office_count'] as int? ?? 0,
      schoolCount: json['school_count'] as int? ?? 0,
      bankCount: json['bank_count'] as int? ?? 0,
      transitCount: json['transit_count'] as int? ?? 0,
      mallCount: json['mall_count'] as int? ?? 0,
      parkCount: json['park_count'] as int? ?? 0,
      healthcareCount: json['healthcare_count'] as int? ?? 0,
      totalBusinesses: json['total_businesses'] as int? ?? 0,
      avgRating: (json['avg_rating'] as num?)?.toDouble() ?? 0.0,
      incomeProxy: json['income_proxy'] as String?,
    );
  }

  /// Check if there are any businesses in this area
  bool get hasBusinesses => totalBusinesses > 0;

  /// Get income level label
  String get incomeLevel {
    switch (incomeProxy) {
      case 'high':
        return 'High Income Area';
      case 'mid':
        return 'Middle Income Area';
      case 'low':
        return 'Developing Area';
      default:
        return 'Unknown';
    }
  }
}

/// Enhanced recommendation response from the API
class EnhancedRecommendation {
  final String gridId;
  final String mode; // "fast" or "full"
  final double lat;
  final double lon;
  final int radius;
  final RecommendationSummary recommendation;
  final CategoryScore gym;
  final CategoryScore cafe;
  final LLMInsights? llmInsights;
  final BEVSummary? bev;
  final int processingTimeMs;

  EnhancedRecommendation({
    required this.gridId,
    required this.mode,
    required this.lat,
    required this.lon,
    required this.radius,
    required this.recommendation,
    required this.gym,
    required this.cafe,
    this.llmInsights,
    this.bev,
    required this.processingTimeMs,
  });

  /// Check if this is a full LLM-powered recommendation
  bool get isLLMPowered => mode == 'full' && llmInsights != null;

  /// Get the winning category
  String get winningCategory => recommendation.bestCategory;

  /// Get the winning score
  CategoryScore get winningScore =>
      recommendation.bestCategory == 'gym' ? gym : cafe;

  /// Compare gym vs cafe
  String get comparison {
    if (gym.score > cafe.score) {
      return 'Gym is ${((gym.score - cafe.score) * 100).round()}% better suited';
    } else if (cafe.score > gym.score) {
      return 'Cafe is ${((cafe.score - gym.score) * 100).round()}% better suited';
    }
    return 'Both categories equally suited';
  }

  factory EnhancedRecommendation.fromJson(Map<String, dynamic> json) {
    return EnhancedRecommendation(
      gridId: json['grid_id'] as String? ?? 'unknown',
      mode: json['mode'] as String? ?? 'fast',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lon: (json['lon'] as num?)?.toDouble() ?? 0.0,
      radius: json['radius'] as int? ?? 500,
      recommendation: RecommendationSummary.fromJson(
        json['recommendation'] as Map<String, dynamic>,
      ),
      gym: CategoryScore.fromJson(json['gym'] as Map<String, dynamic>),
      cafe: CategoryScore.fromJson(json['cafe'] as Map<String, dynamic>),
      llmInsights: json['llm_insights'] != null
          ? LLMInsights.fromJson(json['llm_insights'] as Map<String, dynamic>)
          : null,
      bev: json['bev'] != null
          ? BEVSummary.fromJson(json['bev'] as Map<String, dynamic>)
          : null,
      processingTimeMs: json['processing_time_ms'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'grid_id': gridId,
    'mode': mode,
    'lat': lat,
    'lon': lon,
    'radius': radius,
    'recommendation': {
      'best_category': recommendation.bestCategory,
      'score': recommendation.score,
      'suitability': recommendation.suitability,
      'message': recommendation.message,
    },
    'gym': gym.toJson(),
    'cafe': cafe.toJson(),
    'processing_time_ms': processingTimeMs,
  };
}

/// Request parameters for getting a recommendation
class RecommendationRequest {
  final double lat;
  final double lon;
  final int radius;

  RecommendationRequest({
    required this.lat,
    required this.lon,
    this.radius = 500,
  });

  Map<String, String> toQueryParams() => {
    'lat': lat.toString(),
    'lon': lon.toString(),
    'radius': radius.toString(),
  };
}

// ============================================================================
// Enhanced Response Models (with income data and area analysis)
// ============================================================================

/// Category count with percentage and sample business names
class CategoryCount {
  final String category;
  final int count;
  final double percentage;
  final List<String> businessNames;

  CategoryCount({
    required this.category,
    required this.count,
    required this.percentage,
    this.businessNames = const [],
  });

  factory CategoryCount.fromJson(Map<String, dynamic> json) {
    return CategoryCount(
      category: json['category'] as String,
      count: json['count'] as int,
      percentage: (json['percentage'] as num).toDouble(),
      businessNames:
          (json['business_names'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }

  /// Get a human-readable category name
  String get displayName {
    return category
        .replaceAll('_', ' ')
        .split(' ')
        .map(
          (word) => word.isNotEmpty
              ? '${word[0].toUpperCase()}${word.substring(1)}'
              : '',
        )
        .join(' ');
  }
}

/// Data-backed insight from area analysis
class BackingFactor {
  final String factor;
  final String evidence;
  final String implication;
  final String strength;

  BackingFactor({
    required this.factor,
    required this.evidence,
    required this.implication,
    required this.strength,
  });

  factory BackingFactor.fromJson(Map<String, dynamic> json) {
    return BackingFactor(
      factor: json['factor'] as String,
      evidence: json['evidence'] as String,
      implication: json['implication'] as String,
      strength: json['strength'] as String,
    );
  }

  bool get isStrong => strength == 'strong';
  bool get isModerate => strength == 'moderate';
  bool get isWeak => strength == 'weak';
}

/// Area analysis with top business categories and backing factors
class AreaAnalysis {
  final int totalBusinesses;
  final List<CategoryCount> top5Categories;
  final String areaCharacter;
  final List<BackingFactor> backingFactors;

  AreaAnalysis({
    required this.totalBusinesses,
    required this.top5Categories,
    this.areaCharacter = '',
    this.backingFactors = const [],
  });

  factory AreaAnalysis.fromJson(Map<String, dynamic> json) {
    return AreaAnalysis(
      totalBusinesses: json['total_businesses'] as int,
      top5Categories: (json['top_5_categories'] as List<dynamic>)
          .map((e) => CategoryCount.fromJson(e as Map<String, dynamic>))
          .toList(),
      areaCharacter: json['area_character'] as String? ?? '',
      backingFactors:
          (json['backing_factors'] as List<dynamic>?)
              ?.map((e) => BackingFactor.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

/// Consumer behavior data
class ConsumerBehavior {
  final int avgMealSpending;
  final int avgCoffeeSpending;
  final int gymBudgetMonthly;
  final String priceSensitivity;

  ConsumerBehavior({
    required this.avgMealSpending,
    required this.avgCoffeeSpending,
    required this.gymBudgetMonthly,
    required this.priceSensitivity,
  });

  factory ConsumerBehavior.fromJson(Map<String, dynamic> json) {
    return ConsumerBehavior(
      avgMealSpending: json['avg_meal_spending'] as int? ?? 0,
      avgCoffeeSpending: json['avg_coffee_spending'] as int? ?? 0,
      gymBudgetMonthly: json['gym_budget_monthly'] as int? ?? 0,
      priceSensitivity: json['price_sensitivity'] as String? ?? 'moderate',
    );
  }
}

/// Income and demographic data for the area
class IncomeData {
  final int avgHouseholdIncome;
  final int medianIncome;
  final String incomeBracket;
  final String spendingPower;
  final double affordabilityScore;
  final List<String> keyDemographics;
  final ConsumerBehavior consumerBehavior;

  IncomeData({
    required this.avgHouseholdIncome,
    required this.medianIncome,
    required this.incomeBracket,
    required this.spendingPower,
    required this.affordabilityScore,
    required this.keyDemographics,
    required this.consumerBehavior,
  });

  factory IncomeData.fromJson(Map<String, dynamic> json) {
    return IncomeData(
      avgHouseholdIncome: json['avg_household_income'] as int,
      medianIncome:
          json['median_income'] as int? ?? json['avg_household_income'] as int,
      incomeBracket: json['income_bracket'] as String,
      spendingPower: json['spending_power'] as String,
      affordabilityScore: (json['affordability_score'] as num).toDouble(),
      keyDemographics: (json['key_demographics'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      consumerBehavior: ConsumerBehavior.fromJson(
        json['consumer_behavior'] as Map<String, dynamic>,
      ),
    );
  }

  /// Format income in PKR
  String get formattedIncome =>
      'PKR ${_formatNumber(avgHouseholdIncome)}/month';

  String _formatNumber(int num) {
    if (num >= 100000) {
      return '${(num / 100000).toStringAsFixed(1)}L';
    } else if (num >= 1000) {
      return '${(num / 1000).toStringAsFixed(0)}K';
    }
    return num.toString();
  }
}

/// Supporting factor with count
class SupportingFactor {
  final String factor;
  final int count;
  final String impact;
  final String reason;

  SupportingFactor({
    required this.factor,
    required this.count,
    required this.impact,
    required this.reason,
  });

  factory SupportingFactor.fromJson(Map<String, dynamic> json) {
    return SupportingFactor(
      factor: json['factor'] as String,
      count: json['count'] as int,
      impact: json['impact'] as String,
      reason: json['reason'] as String,
    );
  }

  bool get isPositive => impact == 'positive';
}

/// Enhanced recommendation output with key numbers
class EnhancedRecommendationOutput {
  final String bestCategory;
  final double confidenceScore;
  final String suitability;
  final String summary;
  final Map<String, dynamic> keyNumbers;

  EnhancedRecommendationOutput({
    required this.bestCategory,
    required this.confidenceScore,
    required this.suitability,
    required this.summary,
    required this.keyNumbers,
  });

  factory EnhancedRecommendationOutput.fromJson(Map<String, dynamic> json) {
    return EnhancedRecommendationOutput(
      bestCategory: json['best_category'] as String,
      confidenceScore: (json['confidence_score'] as num).toDouble(),
      suitability: json['suitability'] as String,
      summary: json['summary'] as String,
      keyNumbers: json['key_numbers'] as Map<String, dynamic>,
    );
  }

  int get scorePercent => (confidenceScore * 100).round();
}

/// Full enhanced recommendation response from the API
class EnhancedRecommendationFull {
  final String gridId;
  final Map<String, double> location;
  final AreaAnalysis areaAnalysis;
  final IncomeData incomeData;
  final EnhancedRecommendationOutput recommendation;
  final Map<String, List<SupportingFactor>> supportingFactors;
  final CategoryScore gym;
  final CategoryScore cafe;
  final int processingTimeMs;
  final int totalBusinesses;
  final String modelUsed;

  EnhancedRecommendationFull({
    required this.gridId,
    required this.location,
    required this.areaAnalysis,
    required this.incomeData,
    required this.recommendation,
    required this.supportingFactors,
    required this.gym,
    required this.cafe,
    required this.processingTimeMs,
    required this.totalBusinesses,
    required this.modelUsed,
  });

  factory EnhancedRecommendationFull.fromJson(Map<String, dynamic> json) {
    final analysis = json['analysis'] as Map<String, dynamic>?;
    final location = json['location'] as Map<String, dynamic>;

    // Parse supporting factors
    final factorsJson =
        json['supporting_factors'] as Map<String, dynamic>? ?? {};
    final supportingFactors = <String, List<SupportingFactor>>{};

    for (final entry in factorsJson.entries) {
      supportingFactors[entry.key] = (entry.value as List<dynamic>)
          .map((e) => SupportingFactor.fromJson(e as Map<String, dynamic>))
          .toList();
    }

    return EnhancedRecommendationFull(
      gridId: json['grid_id'] as String? ?? 'custom',
      location: {
        'lat': (location['lat'] as num).toDouble(),
        'lon': (location['lon'] as num).toDouble(),
        'radius': (location['radius'] as num).toDouble(),
      },
      areaAnalysis: AreaAnalysis.fromJson(
        json['area_analysis'] as Map<String, dynamic>,
      ),
      incomeData: IncomeData.fromJson(
        json['income_data'] as Map<String, dynamic>,
      ),
      recommendation: EnhancedRecommendationOutput.fromJson(
        json['recommendation'] as Map<String, dynamic>,
      ),
      supportingFactors: supportingFactors,
      gym: CategoryScore.fromJson(json['gym'] as Map<String, dynamic>),
      cafe: CategoryScore.fromJson(json['cafe'] as Map<String, dynamic>),
      processingTimeMs: (analysis?['processing_time_ms'] as num?)?.round() ?? 0,
      totalBusinesses: analysis?['total_businesses_nearby'] as int? ?? 0,
      modelUsed: analysis?['model_used'] as String? ?? 'rule-based',
    );
  }

  /// Get the winning category score
  CategoryScore get winningScore =>
      recommendation.bestCategory == 'gym' ? gym : cafe;

  /// Get factors for the winning category
  List<SupportingFactor> get winningPositiveFactors =>
      supportingFactors['for_${recommendation.bestCategory}'] ?? [];

  /// Get concerns for the winning category
  List<SupportingFactor> get winningNegativeFactors =>
      supportingFactors['against_${recommendation.bestCategory}'] ?? [];
}
