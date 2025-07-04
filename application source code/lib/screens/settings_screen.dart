// lib/screens/settings_screen.dart

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  TextEditingController _ipController = TextEditingController();
  String? savedIP;

  @override
  void initState() {
    super.initState();
    loadSavedIP();
  }

  Future<void> loadSavedIP() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      savedIP = prefs.getString('server_ip') ?? '';
      _ipController.text = savedIP!;
    });
  }

  Future<void> saveIP() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_ip', _ipController.text.trim());
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Server IP saved successfully')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Settings")),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Enter Server IP Address", style: TextStyle(fontSize: 16)),
            SizedBox(height: 8),
            TextField(
              controller: _ipController,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                hintText: "e.g. 192.168.43.1",
              ),
              keyboardType: TextInputType.numberWithOptions(decimal: true),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: saveIP,
              child: Text("Save IP"),
            )
          ],
        ),
      ),
    );
  }
}
