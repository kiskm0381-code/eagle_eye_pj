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
  String advice; // データを後から入れるので varではなくString

  JobData({
    required this.id,
    required this.label,
    required this.icon,
    required this.badgeColor,
    this.advice = "データを取得中...",
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

  // 職業リストの定義（初期状態）
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
          // ダッシュボードへ移動時にデータを渡す
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
// 📱 2. ダッシュボード画面 (通信機能付き)
// ==========================================
class DashboardPage extends StatefulWidget {
  final JobData selectedJob;
  const DashboardPage({super.key, required this.selectedJob});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  // データの入れ物（初期値はロード中）
  bool isLoading = true;
  String dateDisplay = "---";
  String rank = "-";
  String rankLabel = "読込中";
  String weather = "-";
  int score = 0;
  List<Map<String, dynamic>> timelineData = [];

  @override
  void initState() {
    super.initState();
    _fetchData(); // 画面が開いたらすぐにデータを読みに行く
  }

  // ★GitHubからデータを取ってくる関数
  Future<void> _fetchData() async {
    const url = "https://raw.githubusercontent.com/kiskm0381-code/eagle_eye_pj/main/eagle_eye_data.json";
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // データを画面の変数にセット
        setState(() {
          dateDisplay = data['date'] ?? "日付不明";
          rank = data['rank'] ?? "-";
          rankLabel = _getRankLabel(rank);
          weather = data['weather']['condition'] ?? "不明";
          
          // 職業別のアドバイスを更新
          String jobKey = widget.selectedJob.id;
          if (data['advice'] != null && data['advice'][jobKey] != null) {
            widget.selectedJob.advice = data['advice'][jobKey];
          }

          // タイムラインのデータを整形
          timelineData = [];
          final timeline = data['timeline'];
          if (timeline != null) {
            // 順番通りにリストに追加
             _addTimelineItem(timeline['morning'], "朝 (Morning)", Icons.wb_twilight);
             _addTimelineItem(timeline['daytime'], "日中 (Daytime)", Icons.wb_sunny);
             _addTimelineItem(timeline['evening'], "夕方 (Evening)", Icons.nights_stay);
             _addTimelineItem(timeline['night'], "夜 (Night)", Icons.bedtime);
          }
          isLoading = false; // ロード完了
        });
      } else {
        throw Exception('Failed to load data');
      }
    } catch (e) {
      print("Error: $e");
      setState(() {
        widget.selectedJob.advice = "データの取得に失敗しました。ネット環境を確認してください。";
        isLoading = false;
      });
    }
  }

  void _addTimelineItem(dynamic periodData, String title, IconData icon) {
    if (periodData != null) {
      timelineData.add({
        "time": periodData['time'],
        "title": title,
        "detail": periodData['events'],
        "warning": periodData['warnings'], // 警告があれば入れる
        "icon": icon,
        "color": Colors.blue,
      });
    }
  }

  String _getRankLabel(String rank) {
    switch (rank) {
      case "S": return "激混み";
      case "A": return "混雑";
      case "B": return "普通";
      case "C": return "閑散";
      default: return "-";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: isLoading 
          ? const Center(child: CircularProgressIndicator()) // ロード中はグルグルを表示
          : SafeArea(
              child: Column(
                children: [
                  _buildHeader(),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 20),
                            _buildSRankCard(),
                            const SizedBox(height: 24),
                            _buildAIAdviceCard(),
                            const SizedBox(height: 30),
                            const Text("Today's Flow", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
                            const SizedBox(height: 16),
                            _buildTimeline(),
                            const SizedBox(height: 40),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
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
          if (index == 2) { // プロフィールタップで戻る
             Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const JobSelectionPage()));
          }
        },
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("Eagle Eye", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: widget.selectedJob.badgeColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: widget.selectedJob.badgeColor.withOpacity(0.5)),
                ),
                child: Row(
                  children: [
                    Icon(widget.selectedJob.icon, color: widget.selectedJob.badgeColor, size: 14),
                    const SizedBox(width: 6),
                    Text(widget.selectedJob.label, style: TextStyle(fontSize: 12, color: widget.selectedJob.badgeColor, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
          Text(dateDisplay, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
        ],
      ),
    );
  }

  Widget _buildSRankCard() {
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
          Text(rankLabel, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Text("天気: $weather", style: const TextStyle(fontSize: 14, color: Colors.white70)),
        ],
      ),
    );
  }

  Widget _buildAIAdviceCard() {
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
          Text(widget.selectedJob.advice, style: const TextStyle(fontSize: 15, height: 1.6, color: AppColors.textPrimary)),
        ],
      ),
    );
  }

  Widget _buildTimeline() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: timelineData.length,
      itemBuilder: (context, index) {
        final data = timelineData[index];
        final isLast = index == timelineData.length - 1;
        return IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(width: 60, child: Text(data['time'], style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey))),
              Column(
                children: [
                  Icon(data['icon'], size: 16, color: Colors.blue),
                  if (!isLast) Expanded(child: Container(width: 2, color: AppColors.cardBackground)),
                ],
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(data['title'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.textPrimary)),
                      const SizedBox(height: 4),
                      Text(data['detail'], style: const TextStyle(color: AppColors.textSecondary)),
                      if (data['warning'] != null && data['warning'] != "") ...[
                        const SizedBox(height: 8),
                        Text("⚠️ ${data['warning']}", style: const TextStyle(color: AppColors.warning, fontWeight: FontWeight.bold)),
                      ]
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
