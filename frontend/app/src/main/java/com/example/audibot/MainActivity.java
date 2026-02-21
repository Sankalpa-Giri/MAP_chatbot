package com.example.audibot;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ObjectAnimator;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.view.animation.AnticipateInterpolator;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.splashscreen.SplashScreen;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.drawerlayout.widget.DrawerLayout;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.navigation.NavigationView;
import com.google.firebase.crashlytics.buildtools.reloc.com.google.common.reflect.TypeToken;
import com.google.gson.Gson;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "SHIFT";
    private static final String BASE_URL = "https://7207-103-106-200-60.ngrok-free.app";
    private static final String WAKE_WORD = "hey shift";

    private boolean keepSplashScreen = true;

    DrawerLayout drawerLayout;
    NavigationView navigationView;
    RecyclerView recyclerView;
    ChatAdapter adapter;
    List<Message> messageList = new ArrayList<>();
    SharedPreferences prefs;
    Gson gson = new Gson();

    // ── TTS ────────────────────────────────────────────────────────────────
    private TextToSpeech tts;
    private boolean ttsReady = false;

    // ── Wake word listener (runs in background using Android STT) ──────────
    private SpeechRecognizer wakeWordRecognizer;
    private boolean wakeWordActive = false;

    // ── Command STT (launched as activity for better UI) ───────────────────
    private ActivityResultLauncher<Intent> commandSttLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        SplashScreen splashScreen = SplashScreen.installSplashScreen(this);
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // ── Init TTS ───────────────────────────────────────────────────────
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                int result = tts.setLanguage(new Locale("en", "IN"));
                if (result == TextToSpeech.LANG_MISSING_DATA ||
                    result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts.setLanguage(Locale.ENGLISH);
                }
                tts.setSpeechRate(0.95f);
                tts.setPitch(1.0f);
                ttsReady = true;
            }
        });

        recyclerView = findViewById(R.id.chat_recycler);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ChatAdapter(messageList);
        recyclerView.setAdapter(adapter);

        prefs = getSharedPreferences("chat_prefs", MODE_PRIVATE);
        loadChat();

        WindowCompat.setDecorFitsSystemWindows(getWindow(), true);
        View root = findViewById(R.id.main);
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, insets) -> {
            int top    = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top;
            int bottom = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom;
            v.setPadding(0, top, 0, bottom);
            return insets;
        });

        new Handler(Looper.getMainLooper()).postDelayed(() -> keepSplashScreen = false, 800);
        splashScreen.setKeepOnScreenCondition(() -> keepSplashScreen);
        splashScreen.setOnExitAnimationListener(splashScreenView -> {
            ObjectAnimator slideUp = ObjectAnimator.ofFloat(
                    splashScreenView.getView(), View.TRANSLATION_Y,
                    0f, -splashScreenView.getView().getHeight());
            slideUp.setInterpolator(new AnticipateInterpolator());
            slideUp.setDuration(220L);
            slideUp.addListener(new AnimatorListenerAdapter() {
                @Override public void onAnimationEnd(Animator animation) {
                    splashScreenView.remove();
                }
            });
            slideUp.start();
        });

        drawerLayout   = findViewById(R.id.drawer_layout);
        navigationView = findViewById(R.id.navigation_drawer);

        findViewById(R.id.btn_menu).setOnClickListener(v -> drawerLayout.open());
        findViewById(R.id.btn_add).setOnClickListener(v -> {
            messageList.clear();
            adapter.notifyDataSetChanged();
            prefs.edit().clear().apply();
        });

        navigationView.setNavigationItemSelectedListener(item -> {
            drawerLayout.closeDrawers();
            return true;
        });

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (drawerLayout.isOpen()) drawerLayout.closeDrawers();
                else finish();
            }
        });

        // ── Text send ──────────────────────────────────────────────────────
        EditText    messageBox = findViewById(R.id.edit_message);
        ImageButton sendBtn    = findViewById(R.id.btn_send);
        sendBtn.setOnClickListener(v -> {
            String msg = messageBox.getText().toString().trim();
            if (msg.isEmpty()) return;
            sendMessage(msg);
            messageBox.setText("");
        });

        // ── Command STT launcher (shown when wake word OR button triggered) ─
        commandSttLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        ArrayList<String> matches = result.getData()
                                .getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                        if (matches != null && !matches.isEmpty()) {
                            sendMessage(matches.get(0));
                        }
                    }
                    // Always restart wake word listening after command finishes
                    new Handler(Looper.getMainLooper()).postDelayed(
                            this::startWakeWordListening, 1500);
                });

        // ── Manual mic button ──────────────────────────────────────────────
        ImageButton voiceBtn = findViewById(R.id.btn_voice);
        if (voiceBtn != null) {
            voiceBtn.setOnClickListener(v -> {
                stopWakeWordListening();
                launchCommandStt();
            });
        }

        // ── Start background wake word listening ───────────────────────────
        startWakeWordListening();
    }

    // ══════════════════════════════════════════════════════════════════════
    // WAKE WORD — uses SpeechRecognizer silently in background
    // Listens for "hey shift" without showing any dialog
    // ══════════════════════════════════════════════════════════════════════

    private void startWakeWordListening() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return;
        if (wakeWordActive) return;

        if (wakeWordRecognizer != null) {
            wakeWordRecognizer.destroy();
            wakeWordRecognizer = null;
        }

        wakeWordRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        wakeWordRecognizer.setRecognitionListener(new RecognitionListener() {

            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(
                        SpeechRecognizer.RESULTS_RECOGNITION);

                if (matches != null) {
                    for (String match : matches) {
                        Log.d(TAG, "Wake heard: " + match);
                        if (match.toLowerCase().contains(WAKE_WORD)) {
                            Log.d(TAG, "✅ Hey Shift detected!");
                            wakeWordActive = false;
                            onWakeWordDetected();
                            return;
                        }
                    }
                }
                // Not the wake word — keep listening
                wakeWordActive = false;
                startWakeWordListening();
            }

            @Override
            public void onError(int error) {
                wakeWordActive = false;
                // Restart after short delay on error
                new Handler(Looper.getMainLooper()).postDelayed(
                        MainActivity.this::startWakeWordListening, 1000);
            }

            @Override public void onReadyForSpeech(Bundle p)  { wakeWordActive = true; }
            @Override public void onBeginningOfSpeech()        {}
            @Override public void onRmsChanged(float v)        {}
            @Override public void onBufferReceived(byte[] b)   {}
            @Override public void onEndOfSpeech()              {}
            @Override public void onPartialResults(Bundle b)   {}
            @Override public void onEvent(int t, Bundle b)     {}
        });

        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN");
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);
        // No prompt — silent background listening
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1500);
        intent.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1500);

        try {
            wakeWordRecognizer.startListening(intent);
        } catch (Exception e) {
            Log.e(TAG, "Wake word start failed: " + e);
        }
    }

    private void stopWakeWordListening() {
        wakeWordActive = false;
        if (wakeWordRecognizer != null) {
            wakeWordRecognizer.stopListening();
            wakeWordRecognizer.cancel();
        }
    }

    private void onWakeWordDetected() {
        Log.d(TAG, "Wake word triggered — launching command STT");
        if (tts != null) tts.stop(); // stop speaking before listening
        launchCommandStt();
    }

    // ── Launch STT dialog for the actual command ───────────────────────────
    private void launchCommandStt() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-IN");
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Listening…");
        intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);

        try {
            commandSttLauncher.launch(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Voice input failed", Toast.LENGTH_SHORT).show();
            startWakeWordListening();
        }
    }

    // ── Speak reply ────────────────────────────────────────────────────────
    private void speak(String text) {
        if (ttsReady && tts != null) {
            tts.stop();
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null,
                    "reply_" + System.currentTimeMillis());
        }
    }

    // ── Send message to backend ────────────────────────────────────────────
    private void sendMessage(String msg) {
        messageList.add(new Message(msg, true));
        adapter.notifyItemInserted(messageList.size() - 1);
        recyclerView.scrollToPosition(messageList.size() - 1);
        saveChat();
        sendToBackend(msg);
    }

    private void sendToBackend(String msg) {
        new Thread(() -> {
            try {
                java.net.URL url = new java.net.URL(BASE_URL + "/voice");
                java.net.HttpURLConnection conn =
                        (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("ngrok-skip-browser-warning", "true");
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(15000);

                String safeMsg = msg.replace("\\", "\\\\")
                                    .replace("\"", "\\\"")
                                    .replace("\n", "\\n");
                byte[] body = ("{\"text\":\"" + safeMsg + "\"}").getBytes("UTF-8");
                conn.getOutputStream().write(body);
                conn.getOutputStream().close();

                java.io.BufferedReader br = new java.io.BufferedReader(
                        new java.io.InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();

                String reply = new org.json.JSONObject(sb.toString())
                        .optString("reply", "No reply");

                runOnUiThread(() -> {
                    messageList.add(new Message(reply, false));
                    adapter.notifyItemInserted(messageList.size() - 1);
                    recyclerView.scrollToPosition(messageList.size() - 1);
                    saveChat();
                    speak(reply); // 🔊 bot speaks
                });

            } catch (Exception e) {
                Log.e(TAG, "Backend error: " + e);
                runOnUiThread(() -> {
                    messageList.add(new Message("⚠️ Can't reach server.", false));
                    adapter.notifyItemInserted(messageList.size() - 1);
                    speak("Can't reach server.");
                });
            }
        }).start();
    }

    // ── Chat persistence ───────────────────────────────────────────────────
    private void loadChat() {
        String json = prefs.getString("chat_data", null);
        if (json != null) {
            Type type = new TypeToken<ArrayList<Message>>() {}.getType();
            messageList = gson.fromJson(json, type);
            adapter = new ChatAdapter(messageList);
            recyclerView.setAdapter(adapter);
            if (!messageList.isEmpty())
                recyclerView.scrollToPosition(messageList.size() - 1);
        }
    }

    private void saveChat() {
        prefs.edit().putString("chat_data", gson.toJson(messageList)).apply();
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────
    @Override
    protected void onResume() {
        super.onResume();
        startWakeWordListening();
    }

    @Override
    protected void onPause() {
        super.onPause();
        stopWakeWordListening();
    }

    @Override
    protected void onDestroy() {
        stopWakeWordListening();
        if (wakeWordRecognizer != null) wakeWordRecognizer.destroy();
        if (tts != null) { tts.stop(); tts.shutdown(); }
        super.onDestroy();
    }
}