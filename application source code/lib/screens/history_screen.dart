import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class HistoryScreen extends StatefulWidget {
  final String plate;
  HistoryScreen({required this.plate});

  @override
  _HistoryScreenState createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<dynamic> history = [];
  String? serverIP;

  @override
  void initState() {
    super.initState();
    loadServerIP();
  }

  Future<void> loadServerIP() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    serverIP = prefs.getString('server_ip') ?? '192.168.43.1';
    fetchHistory();
  }

  Future<void> fetchHistory() async {
    if (serverIP == null) return;
    final response = await http.get(Uri.parse('http://$serverIP:5000/history/${widget.plate}'));
    if (response.statusCode == 200) {
      setState(() {
        history = jsonDecode(response.body);
      });
    } else {
      print("Failed to load history");
    }
  }

  Widget buildEntry(Map<String, dynamic> entry) {
    final speed = entry['speed'] ?? {};
    final actualSpeed = speed['actual'] ?? 0.0;
    final targetSpeed = speed['target'] ?? 0.0;
    final base64Image = entry['cv_image'];
    final hasImage = base64Image != null && base64Image.isNotEmpty;

    final cvLabel = entry['cv_label'] ?? 'N/A';
    final vdLabel = entry['vd_label'] ?? 'N/A';
    final bio = entry['bio'] ?? {};
    final bp = bio['blood_pressure'] ?? {};

    return Card(
      margin: EdgeInsets.symmetric(vertical: 8),
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("🕓 ${entry['timestamp']}", style: TextStyle(fontWeight: FontWeight.bold)),
            Text("🧠 CV: $cvLabel"),
            Text("🚗 VD: $vdLabel"),
          ],
        ),
        children: [
          if (hasImage)
            Container(
              margin: EdgeInsets.symmetric(vertical: 8),
              child: Image.memory(
                base64Decode(base64Image),
                height: 200,
                fit: BoxFit.contain,
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (bio.isNotEmpty) ...[
                  Text("❤️ Heart Rate: ${bio['heart_rate']} bpm"),
                  Text("🌡️ Temperature: ${bio['temperature']} °C"),
                  Text("🩸 Oxygen: ${bio['oxygen']} %"),
                  Text("🫁 Respiration: ${bio['respiration_rate']} bpm"),
                  Text("🥂 Alcohol: ${bio['alcohol']} %"),
                  Text("🩺 Blood Pressure: ${bp['systolic']}/${bp['diastolic']} mmHg"),
                ],
                SizedBox(height: 8),
                Text("⚙️ Actual Speed: ${actualSpeed.toStringAsFixed(1)} km/h"),
                Text("🛑 Target Speed Limit: ${targetSpeed.toStringAsFixed(1)} km/h"),
                if (actualSpeed > targetSpeed && targetSpeed > 0)
                  Text(
                    "⚠️ Speeding Detected!",
                    style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                  ),
              ],
            ),
          ),
          SizedBox(height: 12),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('History for ${widget.plate}'),
      ),
      body: history.isEmpty
          ? Center(child: CircularProgressIndicator())
          : ListView.builder(
        padding: EdgeInsets.all(16),
        itemCount: history.length,
        itemBuilder: (context, index) => buildEntry(history[index]),
      ),
    );
  }
}
