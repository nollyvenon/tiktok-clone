class Earning {
  final String id;
  final String sourceType;
  final int amount;
  final String createdAt;

  Earning({required this.id, required this.sourceType, required this.amount, required this.createdAt});

  factory Earning.fromJson(Map<String, dynamic> json) {
    return Earning(
      id: json['id'] as String,
      sourceType: json['source_type'] as String,
      amount: json['amount'] as int,
      createdAt: json['created_at'] as String,
    );
  }
}

class EarningsSummary {
  final int totalEarned;
  final int totalPaidOut;
  final int pendingPayoutTotal;
  final int availableBalance;
  final List<Earning> earnings;

  EarningsSummary({
    required this.totalEarned,
    required this.totalPaidOut,
    required this.pendingPayoutTotal,
    required this.availableBalance,
    required this.earnings,
  });

  factory EarningsSummary.fromJson(Map<String, dynamic> json) {
    return EarningsSummary(
      totalEarned: json['total_earned'] as int,
      totalPaidOut: json['total_paid_out'] as int,
      pendingPayoutTotal: json['pending_payout_total'] as int,
      availableBalance: json['available_balance'] as int,
      earnings: (json['earnings'] as List).map((e) => Earning.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}

class Payout {
  final String id;
  final int amount;
  final String status;
  final String? notes;
  final String requestedAt;

  Payout({required this.id, required this.amount, required this.status, this.notes, required this.requestedAt});

  factory Payout.fromJson(Map<String, dynamic> json) {
    return Payout(
      id: json['id'] as String,
      amount: json['amount'] as int,
      status: json['status'] as String,
      notes: json['notes'] as String?,
      requestedAt: json['requested_at'] as String,
    );
  }
}
