import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import '../models/vehicle.dart';
import 'history_screen.dart';
import '../utils/notification_service.dart';

class HomeScreen extends StatefulWidget {
  final Vehicle vehicle;

  const HomeScreen({Key? key, required this.vehicle}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic> vehicleData = {};
  String serverStatus = '';
  Timer? _timer;
  String? serverIP;
  List<dynamic> interiorEvents = [];
  List<dynamic> exteriorEvents = [];

  // Notification tracking flags
  bool _notifiedIllegalAction = false;
  bool _notifiedAggressiveDriving = false;
  bool _notifiedAlcohol = false;
  bool _notifiedHypertension = false;

  // In-app notifications list
  List<String> notifications = [];

  @override
  void initState() {
    super.initState();
    loadServerIP();
  }

  Future<void> loadServerIP() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    serverIP = prefs.getString('server_ip') ?? '192.168.43.1';
    fetchData();
    fetchHistory();
    _timer = Timer.periodic(const Duration(seconds: 10), (timer) {
      fetchData();
      fetchHistory();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void addNotification(String title, String body) {
    final notificationText = "$title: $body";
    if (!notifications.contains(notificationText)) {
      setState(() {
        notifications.add(notificationText);
      });
    }
    NotificationService.show(title: title, body: body);
  }

  Future<void> fetchData() async {
    if (serverIP == null) return;
    final url = 'http://$serverIP:5000/data/${widget.vehicle.plate}';
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          vehicleData = data;
          serverStatus = '';
        });
        checkForCriticalEvents(data);
      } else {
        setState(() {
          serverStatus = '⚠️ السيرفر متصل لكن لم يتم العثور على بيانات لهذه السيارة';
          vehicleData = {};
        });
      }
    } catch (e) {
      setState(() {
        serverStatus = '⚠️ غير قادر على الاتصال بالسيرفر';
        vehicleData = {};
      });
    }
  }

  Future<void> fetchHistory() async {
    if (serverIP == null) return;
    final url = 'http://$serverIP:5000/history/${widget.vehicle.plate}';
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          interiorEvents = data.where((e) => e['source'] == 'interior').toList();
          exteriorEvents = data.where((e) => e['source'] == 'exterior').toList();
        });
      }
    } catch (_) {}
  }

  void checkForCriticalEvents(Map<String, dynamic> data) {
    final interior = data['interior'] ?? {};
    final vd = data['vd_label'] ?? '';
    final bio = data['bio'] ?? {};
    final exterior = data['exterior'] ?? {};

    final cv = interior['cv_label'] ?? '';
    final heartRate = bio['heart_rate'] ?? 0;
    final temperature = bio['temperature'] ?? 0.0;
    final respiration = bio['respiration_rate'] ?? 0;
    final alcohol = bio['alcohol'] ?? 0.0;
    final oxygen = bio['oxygen'] ?? 100;
    final bp = bio['blood_pressure'] ?? {};
    final systolic = bp['systolic'] ?? 0;
    final diastolic = bp['diastolic'] ?? 0;

    const illegalActions = ['sleep', 'smoking', 'phone', 'drinking', 'eating'];

    // Interior notifications
    if (illegalActions.contains(cv)) {
      if (!_notifiedIllegalAction) {
        addNotification(
          "🚫 Illegal Action Detected",
          "Detected driver behavior: $cv",
        );
        _notifiedIllegalAction = true;
      }
    } else {
      _notifiedIllegalAction = false;
    }

    if (vd == 'aggressive') {
      if (!_notifiedAggressiveDriving) {
        addNotification(
          "🚗 Aggressive Driving",
          "Driving style is classified as aggressive.",
        );
        _notifiedAggressiveDriving = true;
      }
    } else {
      _notifiedAggressiveDriving = false;
    }

    if (alcohol > 0.0) {
      if (!_notifiedAlcohol) {
        addNotification(
          "🍷 Alcohol Detected",
          "Alcohol presence detected in driver's system!",
        );
        _notifiedAlcohol = true;
      }
    } else {
      _notifiedAlcohol = false;
    }

    if (oxygen < 90 || heartRate < 60 || heartRate > 120 || respiration < 12 || respiration > 16) {
      addNotification(
        "🩺 Vital Signs Alert",
        "Abnormal biometric readings detected!",
      );
    }

    if (systolic >= 180 || diastolic >= 120) {
      if (!_notifiedHypertension) {
        addNotification(
          "⚠️ Hypertension Crisis",
          "Blood pressure reading is critically high!",
        );
        _notifiedHypertension = true;
      }
    } else {
      _notifiedHypertension = false;
    }

    // Exterior notifications - send notification on any non-empty trigger
    final cvLabelExt = exterior['cv_label'] ?? '';
    final collisionWarning = exterior['collision_warning'] ?? '';
    final laneAlert = exterior['lane_alert'] ?? '';

    if (cvLabelExt.isNotEmpty) {
      addNotification("🌐 Exterior Alert", "CV Label: $cvLabelExt");
    }
    if (collisionWarning.isNotEmpty) {
      addNotification("🌐 Exterior Alert", "Collision Warning: $collisionWarning");
    }
    if (laneAlert.isNotEmpty) {
      addNotification("🌐 Exterior Alert", "Lane Alert: $laneAlert");
    }
  }

  Widget buildLiveInteriorSection() {
    final interior = vehicleData['interior'] ?? {};
    final label = interior['cv_label'] ?? 'No actions detected';
    final base64Image = interior['cv_image'];

    if (label == 'No detection' && (base64Image == null || base64Image.isEmpty)) return SizedBox.shrink();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🧠 Interior Behavior (Live)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            if (base64Image != null && base64Image.isNotEmpty) ...[
              SizedBox(height: 8),
              Image.memory(base64Decode(base64Image), height: 180, fit: BoxFit.cover),
            ],
            SizedBox(height: 6),
            Text('Detected Action: $label'),
          ],
        ),
      ),
    );
  }

  Widget buildLiveExteriorSection() {
    final exterior = vehicleData['exterior'] ?? {};
    final warning = exterior['collision_warning'] ?? '';
    final laneAlert = exterior['lane_alert'] ?? '';
    final base64Image = exterior['exterior_image'];

    if ((base64Image == null || base64Image.isEmpty) && warning.isEmpty && laneAlert.isEmpty) return SizedBox.shrink();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🌐 Exterior Behavior (Live)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            if (base64Image != null && base64Image.isNotEmpty) ...[
              SizedBox(height: 8),
              Image.memory(base64Decode(base64Image), height: 180, fit: BoxFit.cover),
            ],
            if (warning.isNotEmpty)
              Text("🚨 $warning", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            if (laneAlert.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4.0),
                child: Text("⚠️ $laneAlert", style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  Widget buildEventCard(String title, List<dynamic> events) {
    if (events.isEmpty) return SizedBox.shrink();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: ExpansionTile(
        title: Text(title, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        children: events.map<Widget>((e) {
          final ts = e['timestamp'] ?? '';
          final label = e['cv_label'] ?? e['vd_label'] ?? 'Event';
          final img = e['cv_image'] ?? e['exterior_image'];
          final hasImage = img != null && img.isNotEmpty;
          return ListTile(
            leading: hasImage
                ? Image.memory(base64Decode(img), width: 56, fit: BoxFit.cover)
                : Icon(Icons.event_note),
            title: Text(label),
            subtitle: Text(ts),
          );
        }).toList(),
      ),
    );
  }

  Widget buildSpeedSection() {
    final speed = vehicleData['speed'] ?? {};
    final actualSpeed = (speed['actual'] ?? 0.0).toDouble();
    final targetSpeed = (speed['target'] ?? 0.0).toDouble();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('⚙️ Speed Info', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('🚗 Actual Speed: ${actualSpeed.toStringAsFixed(1)} km/h'),
            Text('🛑 Speed Limit: ${targetSpeed.toStringAsFixed(1)} km/h'),
            if (actualSpeed > targetSpeed && targetSpeed > 0)
              Padding(
                padding: EdgeInsets.only(top: 8.0),
                child: Text(
                  "⚠️ You are speeding!",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.red),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget buildVDSection() {
    if (!vehicleData.containsKey('vd_label')) {
      return Card(
        color: Colors.amber[100],
        child: ListTile(title: Text("⚠️ No Vehicle Dynamics data")),
      );
    }

    final vd = vehicleData['vd_label'] ?? 'normal';
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🚗 Vehicle Dynamics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('Driving Style: $vd'),
            if (vd == 'aggressive')
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Text("⚠️ Aggressive driving detected!", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  Widget buildBioSection() {
    if (!vehicleData.containsKey('bio')) {
      return Card(
        color: Colors.amber[100],
        child: ListTile(title: Text("⚠️ No Bio Sensor data")),
      );
    }

    final bio = vehicleData['bio'] ?? {};
    final heartRate = bio['heart_rate'] ?? 0;
    final temp = bio['temperature'] ?? 0.0;
    final oxygen = bio['oxygen'] ?? 0;
    final alcohol = bio['alcohol'] ?? 0.0;
    final resp = bio['respiration_rate'] ?? 0;
    final bp = bio['blood_pressure'] ?? {};
    final systolic = bp['systolic'] ?? 0;
    final diastolic = bp['diastolic'] ?? 0;
    final handRemoved = bio['hand_removed'] == true;

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🩺 Bio Data', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            if (handRemoved)
              Container(
                margin: EdgeInsets.only(top: 8, bottom: 12),
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '⚠️ Hand removed from sensor!',
                  style: TextStyle(color: Colors.red[800], fontWeight: FontWeight.bold),
                ),
              ),
            Text('Heart Rate: $heartRate bpm'),
            Text('Temperature: $temp °C'),
            Text('Oxygen: $oxygen %'),
            Text('Respiration Rate: $resp bpm'),
            Text('Alcohol: $alcohol %'),
            Text('Blood Pressure: $systolic / $diastolic mmHg'),
          ],
        ),
      ),
    );
  }

  Widget buildNotificationsList() {
    if (notifications.isEmpty) {
      return SizedBox.shrink();
    }
    return Card(
      margin: EdgeInsets.symmetric(vertical: 10),
      child: ExpansionTile(
        title: Text('Notifications (${notifications.length})', style: TextStyle(fontWeight: FontWeight.bold)),
        children: notifications.map((n) => ListTile(title: Text(n))).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.vehicle.plate} | ${widget.vehicle.model}'),
        actions: [
          IconButton(
            icon: Icon(Icons.history),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => HistoryScreen(plate: widget.vehicle.plate),
                ),
              );
            },
          )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: serverStatus.isNotEmpty
            ? Center(child: Text(serverStatus, style: TextStyle(color: Colors.red)))
            : ListView(
          children: [
            buildLiveInteriorSection(),
            buildLiveExteriorSection(),
            buildSpeedSection(),
            buildVDSection(),
            buildBioSection(),
            buildEventCard("🧠 Recent Interior Events", interiorEvents),
            buildEventCard("🌐 Recent Exterior Events", exteriorEvents),
            buildNotificationsList(),
            ElevatedButton(
              onPressed: () {
                addNotification(
                  '✅ Test Notification',
                  'Notifications are working!',
                );
              },
              child: Text('Send Test Notification'),
            ),
          ],
        ),
      ),
    );
  }
}
