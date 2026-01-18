import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const EagleEyeApp());
}

// --- カラー設定 ---
class AppColors {
  static const background = Color(0xFF121212);
  static const cardBackground = Color(0xFF1E1E1E);
  static const navBarBackground = Color(0xFF1E1E1E); // 修正済み
  
  static const primary = Colors.blueAccent;
  static const sRankGradientStart = Color(0xFFff5f6d);
  static const sRankGradientEnd = Color(0xFFffc371);
  static const textPrimary = Colors.white;
  static const textSecondary = Colors.grey;
  static const warning = Color(0xFFff4b4b);
}

// 職業データモデル
class JobData {
  final String id;
  final String label;
  final IconData icon;
  final Color badgeColor;
  
  JobData({
    required this.id,
    required this.label,
    required this.icon,
    required this.badgeColor,
  });
}

class EagleEyeApp extends StatelessWidget {
  const EagleEyeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: AppColors.background,
        primaryColor: AppColors.primary,
        appBarTheme: const AppBarTheme(backgroundColor: AppColors.background, elevation: 0),
        colorScheme: const ColorScheme.dark(primary: AppColors.primary, surface: AppColors.cardBackground),
      ),
      home: const JobSelectionPage(),
    );
  }
}

// ==========================================
// 📱 1. 職業選択画面
// ==========================================
class JobSelectionPage extends StatelessWidget {
  const JobSelectionPage({super.key});

  static final List<JobData> initialJobList = [
    JobData(id: "taxi", label: "タクシー運転手", icon: Icons.local_taxi_rounded, badgeColor: const Color(0xFFFBC02D)),
    JobData(id: "restaurant", label: "飲食店", icon: Icons.restaurant_rounded, badgeColor: const Color(0xFFD32F2F)),
    JobData(id: "hotel", label: "ホテル・宿泊", icon: Icons.apartment_rounded, badgeColor: const Color(0xFF1976D2)),
    JobData(id: "shop", label: "お土産・物販", icon: Icons.local_mall_rounded, badgeColor: const Color(0xFFE91E63)),
    JobData(id: "logistics", label: "物流・配送", icon: Icons.local_shipping_rounded, badgeColor: const Color(0xFF009688)),
    JobData(id: "conveni", label: "コンビニ", icon: Icons.storefront_rounded, badgeColor: const Color(0xFFFF9800)),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 40.0),
            child: Column(
              children: [
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.amber.shade700, width: 4),
                    gradient: LinearGradient(colors: [Colors.amber.shade900, Colors.amber.shade700], begin: Alignment.topLeft, end: Alignment.bottomRight),
                  ),
                  child: const Icon(Icons.remove_red_eye_rounded, size: 80, color: Colors.white),
                ),
                const SizedBox(height: 24),
                const Text("Eagle Eye", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
                const SizedBox(height: 8),
                const Text("AIによる観光需要予測システム", style: TextStyle(fontSize: 14, color: AppColors.textSecondary)),
                const SizedBox(height: 60),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: initialJobList.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 16),
                  itemBuilder: (context, index) => _buildJobButton(context, initialJobList[index]),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildJobButton(BuildContext context, JobData job) {
    return Material(
      color: AppColors.cardBackground,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: () {
          Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => DashboardPage(selectedJob: job)));
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: job.badgeColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: job.badgeColor, width: 2),
                ),
                child: Icon(job.icon, color: job.badgeColor, size: 28),
              ),
              const SizedBox(width: 20),
              Expanded(child: Text(job.label, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary))),
              const Icon(Icons.arrow_forward_ios_rounded, color: AppColors.textSecondary, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ==========================================
// 📱 2. ダッシュボード画面 (横スワイプ対応)
// ==========================================
class DashboardPage extends StatefulWidget {
  final JobData selectedJob;
  const DashboardPage({super.key, required this.selectedJob});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool isLoading = true;
  List<dynamic> allData = []; // 3日分のデータを全部入れる
  String errorMessage = "";

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  // ★新しいURLからデータを取得
  Future<void> _fetchData() async {
    // 組織化後の新URL
    const url = "https://raw.githubusercontent.com/eagle-eye-official/eagle_eye_pj/main/eagle_eye_data.json";
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        
        setState(() {
          allData = data;
          isLoading = false;
        });
      } else {
        throw Exception('Failed to load data');
      }
    } catch (e) {
      print("Error: $e");
      setState(() {
        errorMessage = "データの取得に失敗しました。\nネット環境を確認してください。";
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    
    if (errorMessage.isNotEmpty) {
      return Scaffold(
        body: Center(child: Text(errorMessage, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center)),
      );
    }

    // 3日分のデータをPageViewで横スライド表示
    return Scaffold(
      body: PageView.builder(
        itemCount: allData.length,
        itemBuilder: (context, index) {
          return DailyReportView(
            data: allData[index],
            selectedJob: widget.selectedJob,
            pageIndex: index, // 何ページ目か
          );
        },
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppColors.navBarBackground,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textSecondary,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_today), label: 'Calendar'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
        onTap: (index) {
          if (index == 2) {
             Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const JobSelectionPage()));
          }
        },
      ),
    );
  }
}

// 1日分のレポートを表示するWidget
class DailyReportView extends StatelessWidget {
  final Map<String, dynamic> data;
  final JobData selectedJob;
  final int pageIndex;

  const DailyReportView({
    super.key,
    required this.data,
    required this.selectedJob,
    required this.pageIndex,
  });

  @override
  Widget build(BuildContext context) {
    // データ解析（JSONのキー揺らぎに対応）
    String date = data['date'] ?? "日付不明";
    String rank = data['rank'] ?? data['demand_rank'] ?? data['overall_rank'] ?? "-";
    
    // 天気情報の取得（文字列かオブジェクトか判定）
    String weather = "不明";
    if (data['weather'] is String) {
      weather = data['weather'];
    } else if (data['weather'] is Map) {
      weather = data['weather']['condition'] ?? "詳細不明";
    }

    // ランクに応じたラベル
    String rankLabel = "不明";
    if (rank == "S") rankLabel = "激混み";
    else if (rank == "A") rankLabel = "混雑";
    else if (rank == "B") rankLabel = "普通";
    else if (rank == "C") rankLabel = "閑散";

    // 職業アドバイス
    String advice = "アドバイスなし";
    if (data['advice'] != null && data['advice'][selectedJob.id] != null) {
      advice = data['advice'][selectedJob.id];
    } else if (data['advice_by_profession'] != null && data['advice_by_profession'][selectedJob.id] != null) {
      advice = data['advice_by_profession'][selectedJob.id];
    }

    return SafeArea(
      child: Column(
        children: [
          _buildHeader(date),
          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 20),
                    _buildSRankCard(rank, rankLabel, weather),
                    const SizedBox(height: 24),
                    _buildAIAdviceCard(advice),
                    const SizedBox(height: 30),
                    // ※タイムラインは構造が複雑なので今回は省略し、アドバイス重視にします
                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(String date) {
    String dayLabel = "今日";
    if (pageIndex == 1) dayLabel = "明日";
    if (pageIndex == 2) dayLabel = "明後日";

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Eagle Eye ($dayLabel)", style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: selectedJob.badgeColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: selectedJob.badgeColor.withOpacity(0.5)),
                ),
                child: Row(
                  children: [
                    Icon(selectedJob.icon, color: selectedJob.badgeColor, size: 14),
                    const SizedBox(width: 6),
                    Text(selectedJob.label, style: TextStyle(fontSize: 12, color: selectedJob.badgeColor, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
          Text(date, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
        ],
      ),
    );
  }

  Widget _buildSRankCard(String rank, String label, String weather) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 36.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(colors: [AppColors.sRankGradientStart, AppColors.sRankGradientEnd], begin: Alignment.topLeft, end: Alignment.bottomRight),
        boxShadow: [BoxShadow(color: AppColors.sRankGradientStart.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 6))],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(rank, style: const TextStyle(fontSize: 80, fontWeight: FontWeight.bold, color: Colors.white, height: 1.0)),
          Text(label, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Text(weather, style: const TextStyle(fontSize: 14, color: Colors.white70), textAlign: TextAlign.center),
          ),
        ],
      ),
    );
  }

  Widget _buildAIAdviceCard(String advice) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24.0),
      decoration: BoxDecoration(
        color: AppColors.cardBackground,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("AI Advice", style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
          const SizedBox(height: 8),
          Text(advice, style: const TextStyle(fontSize: 15, height: 1.6, color: AppColors.textPrimary)),
        ],
      ),
    );
  }
}
