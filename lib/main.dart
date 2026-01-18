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
  static const navBarBackground = Color(0xFF1E1E1E);
  static const primary = Colors.blueAccent;
  
  static const rankS_Start = Color(0xFFff9966);
  static const rankS_End = Color(0xFFff5e62);
  static const rankA_Start = Color(0xFFcb2d3e);
  static const rankA_End = Color(0xFFef473a);
  static const rankB_Start = Color(0xFF00c6ff);
  static const rankB_End = Color(0xFF0072ff);
  static const rankC_Start = Color(0xFF56ab2f);
  static const rankC_End = Color(0xFFa8e063);
  
  static const textPrimary = Colors.white;
  static const textSecondary = Colors.grey;
}

class JobData {
  final String id;
  final String label;
  final IconData icon;
  final Color badgeColor;
  JobData({required this.id, required this.label, required this.icon, required this.badgeColor});
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
                const Icon(Icons.remove_red_eye_rounded, size: 80, color: Colors.white),
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
        onTap: () => Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => MainContainerPage(selectedJob: job))),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
          child: Row(
            children: [
              Icon(job.icon, color: job.badgeColor, size: 28),
              const SizedBox(width: 20),
              Expanded(child: Text(job.label, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
              const Icon(Icons.arrow_forward_ios_rounded, color: AppColors.textSecondary, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class MainContainerPage extends StatefulWidget {
  final JobData selectedJob;
  const MainContainerPage({super.key, required this.selectedJob});

  @override
  State<MainContainerPage> createState() => _MainContainerPageState();
}

class _MainContainerPageState extends State<MainContainerPage> {
  int _currentIndex = 0;
  List<dynamic> allData = [];
  bool isLoading = true;
  String errorMessage = "";
  final PageController _dashboardPageController = PageController();

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    const url = "https://raw.githubusercontent.com/eagle-eye-official/eagle_eye_pj/main/eagle_eye_data.json";
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        setState(() {
          allData = jsonDecode(response.body);
          isLoading = false;
        });
      } else {
        throw Exception('Failed to load');
      }
    } catch (e) {
      setState(() {
        errorMessage = "データ取得エラー: ネット環境を確認してください";
        isLoading = false;
      });
    }
  }

  void _onDateSelected(int index) {
    setState(() {
      _currentIndex = 0;
    });
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_dashboardPageController.hasClients) {
        _dashboardPageController.jumpToPage(index);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (errorMessage.isNotEmpty) return Scaffold(body: Center(child: Text(errorMessage, style: const TextStyle(color: Colors.red))));

    final List<Widget> pages = [
      DashboardPage(selectedJob: widget.selectedJob, allData: allData, pageController: _dashboardPageController),
      CalendarPage(allData: allData, onDateSelected: _onDateSelected),
    ];

    return Scaffold(
      // ★Headerを共通化してここに配置
      appBar: AppBar(
        toolbarHeight: 0, // デフォルトAppBarは隠す
      ),
      body: Column(
        children: [
          // ★カスタマイズヘッダー
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: const BoxDecoration(
              color: AppColors.background,
              border: Border(bottom: BorderSide(color: Colors.white10)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.location_on, color: AppColors.primary, size: 18),
                    const SizedBox(width: 4),
                    const Text("北海道 函館市", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  ],
                ),
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
                      Text(widget.selectedJob.label, style: TextStyle(color: widget.selectedJob.badgeColor, fontSize: 12, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(child: pages[_currentIndex]),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppColors.navBarBackground,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textSecondary,
        currentIndex: _currentIndex,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_today), label: 'Calendar'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
        onTap: (index) {
          if (index == 2) {
             Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => const JobSelectionPage()));
          } else {
            setState(() {
              _currentIndex = index;
            });
          }
        },
      ),
    );
  }
}

class DashboardPage extends StatelessWidget {
  final JobData selectedJob;
  final List<dynamic> allData;
  final PageController pageController;

  const DashboardPage({super.key, required this.selectedJob, required this.allData, required this.pageController});

  @override
  Widget build(BuildContext context) {
    return PageView.builder(
      controller: pageController,
      itemCount: allData.length,
      itemBuilder: (context, index) {
        return DailyReportView(data: allData[index], selectedJob: selectedJob, pageIndex: index);
      },
    );
  }
}

class CalendarPage extends StatelessWidget {
  final List<dynamic> allData;
  final Function(int) onDateSelected;

  const CalendarPage({super.key, required this.allData, required this.onDateSelected});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 10),
          const Text("Forecast Calendar", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          Expanded(
            child: ListView.separated(
              itemCount: allData.length,
              separatorBuilder: (context, index) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final data = allData[index];
                final String date = data['date'] ?? "";
                final String rank = data['rank'] ?? "-";
                final String weather = data['weather_overview']['condition'] ?? "";
                List<Color> colors = _getRankColors(rank);
                String dayLabel = index == 0 ? "今日" : (index == 1 ? "明日" : "明後日");

                return InkWell(
                  onTap: () => onDateSelected(index),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.cardBackground,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.grey.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 50,
                          height: 50,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(colors: colors),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(rank, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("$dayLabel  $date", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                              const SizedBox(height: 4),
                              Text(weather, style: const TextStyle(color: Colors.grey)),
                            ],
                          ),
                        ),
                        const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

List<Color> _getRankColors(String rank) {
  switch (rank) {
    case 'S': return [AppColors.rankS_Start, AppColors.rankS_End];
    case 'A': return [AppColors.rankA_Start, AppColors.rankA_End];
    case 'B': return [AppColors.rankB_Start, AppColors.rankB_End];
    case 'C': return [AppColors.rankC_Start, AppColors.rankC_End];
    default: return [Colors.grey, Colors.grey];
  }
}

class DailyReportView extends StatelessWidget {
  final Map<String, dynamic> data;
  final JobData selectedJob;
  final int pageIndex;

  const DailyReportView({super.key, required this.data, required this.selectedJob, required this.pageIndex});

  @override
  Widget build(BuildContext context) {
    String date = data['date'] ?? "";
    String rank = data['rank'] ?? "C";
    Map<String, dynamic> wOverview = data['weather_overview'] ?? {};
    String condition = wOverview['condition'] ?? "詳細不明";
    String high = wOverview['high'] ?? "--";
    String low = wOverview['low'] ?? "--";
    String rain = wOverview['rain'] ?? "--";
    
    // イベント情報取得
    Map<String, dynamic> events = data['events_info'] ?? {};
    String eventName = events['event_name'] ?? "特になし";
    String eventTime = events['time_info'] ?? "";
    String trafficWarn = events['traffic_warning'] ?? "";

    List<Color> rankColors = _getRankColors(rank);
    String rankLabel = rank == "S" ? "激混み" : (rank == "A" ? "混雑" : (rank == "B" ? "普通" : "閑散"));
    String dayLabel = pageIndex == 0 ? "今日" : (pageIndex == 1 ? "明日" : "明後日");

    return SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: Text("$dayLabelの予測 ($date)", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.grey)),
          ),
          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20.0),
                child: Column(
                  children: [
                    const SizedBox(height: 10),
                    _buildMainCard(rank, rankLabel, condition, high, low, rain, rankColors),
                    const SizedBox(height: 24),
                    
                    // ★イベント・交通情報カード
                    _buildEventCard(eventName, eventTime, trafficWarn),
                    
                    const SizedBox(height: 30),
                    const Align(alignment: Alignment.centerLeft, child: Text("Time Schedule", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
                    const SizedBox(height: 16),
                    _buildTimeSlot(data['timeline']?['morning'], "朝 (05:00-11:00)", Icons.wb_twilight),
                    _buildTimeSlot(data['timeline']?['daytime'], "昼 (11:00-16:00)", Icons.wb_sunny),
                    _buildTimeSlot(data['timeline']?['night'], "夜 (16:00-24:00)", Icons.nights_stay),
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

  Widget _buildMainCard(String rank, String label, String cond, String high, String low, String rain, List<Color> colors) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: LinearGradient(colors: colors, begin: Alignment.topLeft, end: Alignment.bottomRight),
        boxShadow: [BoxShadow(color: colors[0].withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 6))],
      ),
      child: Column(
        children: [
          Text(rank, style: const TextStyle(fontSize: 80, fontWeight: FontWeight.bold, height: 1.0)),
          Text(label, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.black.withOpacity(0.2), borderRadius: BorderRadius.circular(16)),
            child: Column(
              children: [
                 Text(cond, style: const TextStyle(fontSize: 13, height: 1.4), textAlign: TextAlign.center),
                 const SizedBox(height: 12),
                 Row(
                   mainAxisAlignment: MainAxisAlignment.spaceAround,
                   children: [
                     Column(children: [const Icon(Icons.thermostat, color: Colors.white70, size: 20), const SizedBox(height: 4), Text("最高 $high\n最低 $low", textAlign: TextAlign.center, style: const TextStyle(fontSize: 11))]),
                     Column(children: [const Icon(Icons.umbrella, color: Colors.white70, size: 20), const SizedBox(height: 4), Text(rain, style: const TextStyle(fontSize: 12))]),
                   ],
                 )
              ],
            ),
          )
        ],
      ),
    );
  }

  // ★イベント用カードWidget
  Widget _buildEventCard(String name, String time, String warning) {
    if (name == "特になし" && warning == "") return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.event_note, color: Colors.amber, size: 20),
              SizedBox(width: 8),
              Text("イベント・交通情報", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.amber)),
            ],
          ),
          const SizedBox(height: 12),
          Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          if (time.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(time, style: const TextStyle(fontSize: 13, color: Colors.grey)),
          ],
          if (warning.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: AppColors.warning.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppColors.warning, size: 16),
                  const SizedBox(width: 8),
                  Expanded(child: Text(warning, style: const TextStyle(color: AppColors.warning, fontSize: 13, fontWeight: FontWeight.bold))),
                ],
              ),
            ),
          ]
        ],
      ),
    );
  }

  Widget _buildTimeSlot(Map<String, dynamic>? data, String title, IconData icon) {
    if (data == null) return const SizedBox.shrink();
    String high = data['high'] ?? "-";
    String low = data['low'] ?? "-";
    String rain = data['rain'] ?? "-";
    String weather = data['weather'] ?? "-";
    Map<String, dynamic> advices = data['advice'] ?? {};
    String jobAdvice = advices[selectedJob.id] ?? "特になし";

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.cardBackground, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: Colors.blueAccent),
              const SizedBox(width: 10),
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const Spacer(),
              const Icon(Icons.thermostat, size: 14, color: Colors.redAccent),
              Text(high, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(width: 4),
              const Icon(Icons.thermostat, size: 14, color: Colors.blueAccent),
              Text(low, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const SizedBox(width: 34),
              Text("天気: $weather", style: const TextStyle(fontSize: 13, color: Colors.grey)),
              const Spacer(),
              const Icon(Icons.umbrella, size: 14, color: Colors.grey),
              Text(" $rain", style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
          const Divider(color: Colors.grey, height: 24),
          SelectableText(jobAdvice, style: const TextStyle(fontSize: 14, height: 1.6)),
        ],
      ),
    );
  }
}
