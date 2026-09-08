/*
 * PRM UI FIX - Phase 3B screen bounds for owned UI
 * 32-bit WINMM proxy for Return to Morroc PRM.exe
 *
 * Goals for Phase 2F:
 *   - leave PRM.exe untouched
 *   - load automatically as winmm.dll
 *   - forward the four WINMM functions PRM imports
 *   - write prm-ui-fix.log beside the DLL
 *   - read prm-ui-fix.ini
 *   - install version-independent IAT hooks for CreateFontA/CreateFontIndirectA
 *
 * This source is deliberately freestanding (no Windows SDK / CRT needed to build).
 */

int _fltused = 0;

typedef unsigned char      BYTE;
typedef unsigned short     WORD;
typedef unsigned int       UINT;
typedef unsigned long      DWORD;
typedef long               LONG;
typedef int                BOOL;
typedef unsigned long      ULONG_PTR;
typedef void*              HANDLE;
typedef void*              HMODULE;
typedef void*              HINSTANCE;
typedef void*              HFONT;
typedef void*              LPVOID;
typedef const char*        LPCSTR;
typedef char*              LPSTR;
typedef const void*        LPCVOID;
typedef unsigned long      MMRESULT;

typedef long               HRESULT;
typedef unsigned short     USHORT;
typedef unsigned long      ULONG;
typedef struct _RECT { LONG left, top, right, bottom; } RECT;
typedef struct _POINT { LONG x, y; } POINT;
typedef void* HWND;
typedef struct _GUID {
    DWORD Data1;
    WORD Data2;
    WORD Data3;
    BYTE Data4[8];
} GUID;

typedef struct _TIMECAPS {
    UINT wPeriodMin;
    UINT wPeriodMax;
} TIMECAPS, *LPTIMECAPS;

typedef struct _LOGFONTA {
    LONG lfHeight;
    LONG lfWidth;
    LONG lfEscapement;
    LONG lfOrientation;
    LONG lfWeight;
    BYTE lfItalic;
    BYTE lfUnderline;
    BYTE lfStrikeOut;
    BYTE lfCharSet;
    BYTE lfOutPrecision;
    BYTE lfClipPrecision;
    BYTE lfQuality;
    BYTE lfPitchAndFamily;
    char lfFaceName[32];
} LOGFONTA;

#define WINAPI __attribute__((stdcall))
#define TRUE 1
#define FALSE 0
#define DLL_PROCESS_ATTACH 1
#define PAGE_READWRITE 0x04
#define PAGE_EXECUTE_READWRITE 0x40
#define PAGE_NOACCESS 0x01
#define PAGE_GUARD 0x100
#define MEM_COMMIT 0x1000
#define VK_UI_SETTINGS       0x71 /* F2 */
#define VK_TRACE_CAPTURE     0x73 /* F4 */
#define VK_UI_SHARP          0x72 /* F3 */
#define VK_UI_SCALE          0x74 /* F5 */
#define VK_UI_INPUT          0x75 /* F6 */
#define VK_UI_GROUP_DUMP     0x76 /* F7 */
#define VK_OWNER_DIAGNOSTICS 0x77 /* F8 */
#define VK_WORLD_INPUT       0x78 /* F9 */
#define PRM_WORLD_RAY_CALL_RVA      0x00334568UL
#define PRM_WORLD_RAY_TARGET_RVA    0x000A1540UL
#define PRM_CURSOR_DRAW_CALL_RVA    0x00227B7BUL
#define PRM_CURSOR_DRAW_TARGET_RVA  0x00227BC0UL
#define PRM_SPRITE_SUBMIT_CALL_RVA  0x00227FD9UL
#define PRM_SPRITE_SUBMIT_TARGET_RVA 0x000A0550UL
#define PRM_MOUSE_X_RVA             0x00A83374UL
#define PRM_MOUSE_Y_RVA             0x00A83378UL
#define PRM_MAIN_HWND_RVA           0x00D0AABCUL
#define PRM_BITMAP_PRIMARY_RVA     0x0020BAD4UL
#define PRM_BITMAP_ALTERNATE_RVA   0x0020BAA3UL
#define PRM_BITMAP_QUEUE_CALL_RVA  0x000AB5A1UL
#define PRM_BITMAP_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_OVERLAY_DRAW_CALL_RVA  0x0020BAF0UL
#define PRM_OVERLAY_DRAW_TARGET_RVA 0x0071C8C0UL
#define PRM_OVERLAY_QUEUE_CALL_RVA 0x0071C8DDUL
#define PRM_OVERLAY_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_SPECIAL_DRAW_CALL_RVA  0x0020BA73UL
#define PRM_SPECIAL_DRAW_TARGET_RVA 0x0017B6B0UL
#define PRM_MAP_DRAW_CALL_RVA      0x0020BA38UL
#define PRM_MAP_DRAW_TARGET_RVA    0x0017B3E0UL
#define PRM_MINIMAP_DRAW_CALL_RVA  0x0034024DUL
#define PRM_MINIMAP_DRAW_TARGET_RVA 0x00331E70UL
#define PRM_MINIMAP_WINDOW_RVA     0x00AB7880UL
#define PRM_MINIMAP_QUEUE_CALL_RVA 0x0022835FUL
#define PRM_MINIMAP_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_MINIMAP_MARKER_QUEUE_CALL_RVA 0x003325C4UL
#define PRM_MINIMAP_MARKER_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_TOOLTIP_MANAGER_RVA 0x00A78D8CUL
#define PRM_RECT_QUEUE_CALL_RVA    0x0009277FUL
#define PRM_RECT_QUEUE_TARGET_RVA  0x000A0550UL
#define PRM_IMAGE_QUEUE_CALL_RVA   0x00093058UL
#define PRM_IMAGE_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_PREVIEW_QUEUE_CALL_RVA 0x000AB829UL
#define PRM_PREVIEW_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_MAP_LINE_QUEUE_CALL_RVA 0x00091FD0UL
#define PRM_MAP_LINE_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_MAP_ARROW_QUEUE_CALL_RVA 0x00177DC0UL
#define PRM_MAP_ARROW_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_MAP_SPRITE_QUEUE_CALL_RVA 0x0017AA2DUL
#define PRM_MAP_SPRITE_QUEUE_TARGET_RVA 0x000A0550UL
#define PRM_OFFSCREEN_DP_RETURN_RVA 0x000A22A1UL
#define PRM_OFFSCREEN_DIP_RETURN_RVA 0x000A228DUL
#define PRM_UI_CAPTURE_RVA         0x00AB786CUL
#define PRM_UI_HIT_EVENT_CALL_RVA   0x001F862CUL
#define PRM_UI_HIT_EVENT_TARGET_RVA 0x001FA1A0UL
#define PRM_UI_HIT_MOUSE_CALL_RVA   0x00209FCEUL
#define PRM_UI_HIT_MOUSE_TARGET_RVA 0x001FA1A0UL
#define PRM_UI_HIT_CANDIDATE_RVA    0x001FA1C2UL
#define PRM_UI_MOUSE_RETURN_RVA     0x00495BE1UL
#define FILE_APPEND_DATA 0x00000004UL
#define FILE_SHARE_READ 0x00000001UL
#define FILE_SHARE_WRITE 0x00000002UL
#define OPEN_ALWAYS 4UL
#define FILE_ATTRIBUTE_NORMAL 0x00000080UL
#define INVALID_HANDLE_VALUE ((HANDLE)(ULONG_PTR)-1)
#define FILE_END 2UL

/* Kernel32 functions resolved directly from loaded modules (no import library). */
typedef HMODULE (WINAPI *PFN_LoadLibraryA)(LPCSTR);
typedef UINT    (WINAPI *PFN_GetSystemDirectoryA)(LPSTR, UINT);
typedef BOOL    (WINAPI *PFN_VirtualProtect)(LPVOID, unsigned long, DWORD, DWORD*);
typedef unsigned long SIZE_T;
typedef BOOL    (WINAPI *PFN_FlushInstructionCache)(HANDLE, LPCVOID, SIZE_T);
typedef struct _MEMORY_BASIC_INFORMATION {
    LPVOID BaseAddress;
    LPVOID AllocationBase;
    DWORD AllocationProtect;
    SIZE_T RegionSize;
    DWORD State;
    DWORD Protect;
    DWORD Type;
} MEMORY_BASIC_INFORMATION;
typedef SIZE_T  (WINAPI *PFN_VirtualQuery)(LPCVOID, MEMORY_BASIC_INFORMATION*, SIZE_T);
typedef HMODULE (WINAPI *PFN_GetModuleHandleA)(LPCSTR);
typedef DWORD   (WINAPI *PFN_GetModuleFileNameA)(HMODULE, LPSTR, DWORD);
typedef UINT    (WINAPI *PFN_GetPrivateProfileIntA)(LPCSTR, LPCSTR, int, LPCSTR);
typedef HANDLE  (WINAPI *PFN_CreateFileA)(LPCSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE);
typedef BOOL    (WINAPI *PFN_WriteFile)(HANDLE, LPCVOID, DWORD, DWORD*, LPVOID);
typedef DWORD   (WINAPI *PFN_SetFilePointer)(HANDLE, LONG, LONG*, DWORD);
typedef BOOL    (WINAPI *PFN_CloseHandle)(HANDLE);
typedef DWORD   (WINAPI *PFN_GetTickCount)(void);
typedef BOOL    (WINAPI *PFN_DisableThreadLibraryCalls)(HMODULE);

typedef short   (WINAPI *PFN_GetAsyncKeyState)(int);
typedef BOOL    (WINAPI *PFN_ScreenToClient)(HWND, POINT*);
typedef BOOL    (WINAPI *PFN_GetCursorPos)(POINT*);
typedef BOOL    (WINAPI *PFN_GetClientRect)(HWND, RECT*);
typedef DWORD   (WINAPI *PFN_GetCurrentThreadId)(void);
typedef USHORT  (WINAPI *PFN_RtlCaptureStackBackTrace)(ULONG, ULONG, LPVOID*, ULONG*);

static PFN_LoadLibraryA g_LoadLibraryA;
static PFN_GetSystemDirectoryA g_GetSystemDirectoryA;
static PFN_VirtualProtect g_VirtualProtect;
static PFN_FlushInstructionCache g_FlushInstructionCache;
static PFN_VirtualQuery g_VirtualQuery;
static PFN_GetModuleHandleA g_GetModuleHandleA;
static PFN_GetModuleFileNameA g_GetModuleFileNameA;
static PFN_GetPrivateProfileIntA g_GetPrivateProfileIntA;
static PFN_CreateFileA g_CreateFileA;
static PFN_WriteFile g_WriteFile;
static PFN_SetFilePointer g_SetFilePointer;
static PFN_CloseHandle g_CloseHandle;
static PFN_GetTickCount g_GetTickCount;
static PFN_DisableThreadLibraryCalls g_DisableThreadLibraryCalls;

static PFN_GetAsyncKeyState g_GetAsyncKeyState;
static PFN_ScreenToClient g_real_ScreenToClient;
static PFN_GetCursorPos g_GetCursorPos;
static PFN_GetClientRect g_GetClientRect;
static PFN_GetCurrentThreadId g_GetCurrentThreadId;
static HWND g_input_hwnd;
static PFN_RtlCaptureStackBackTrace g_RtlCaptureStackBackTrace;

/* Real WINMM exports. */
typedef MMRESULT (WINAPI *PFN_timeBeginPeriod)(UINT);
typedef MMRESULT (WINAPI *PFN_timeEndPeriod)(UINT);
typedef MMRESULT (WINAPI *PFN_timeGetDevCaps)(LPTIMECAPS, UINT);
typedef DWORD    (WINAPI *PFN_timeGetTime)(void);

static PFN_timeBeginPeriod g_real_timeBeginPeriod;
static PFN_timeEndPeriod g_real_timeEndPeriod;
static PFN_timeGetDevCaps g_real_timeGetDevCaps;
static PFN_timeGetTime g_real_timeGetTime;

/* GDI functions to hook. */
typedef HFONT (WINAPI *PFN_CreateFontA)(int,int,int,int,int,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,LPCSTR);
typedef HFONT (WINAPI *PFN_CreateFontIndirectA)(const LOGFONTA*);
static PFN_CreateFontA g_real_CreateFontA;
static PFN_CreateFontIndirectA g_real_CreateFontIndirectA;


/* DirectDraw / Direct3D7 tracing hooks. COM methods are stdcall. */
typedef HRESULT (WINAPI *PFN_DirectDrawCreateEx)(void*, void**, const GUID*, void*);
typedef HRESULT (WINAPI *PFN_COM_QueryInterface)(void*, const GUID*, void**);
typedef HRESULT (WINAPI *PFN_D3D7_CreateDevice)(void*, const GUID*, void*, void**);
typedef HRESULT (WINAPI *PFN_D3D7_BeginScene)(void*);
typedef HRESULT (WINAPI *PFN_D3D7_EndScene)(void*);
typedef HRESULT (WINAPI *PFN_D3D7_DrawPrimitive)(void*, DWORD, DWORD, const void*, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_DrawIndexedPrimitive)(void*, DWORD, DWORD, const void*, DWORD, const WORD*, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_DrawPrimitiveStrided)(void*, DWORD, DWORD, const void*, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_DrawIndexedPrimitiveStrided)(void*, DWORD, DWORD, const void*, DWORD, const WORD*, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_DrawPrimitiveVB)(void*, DWORD, void*, DWORD, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_DrawIndexedPrimitiveVB)(void*, DWORD, void*, DWORD, DWORD, const WORD*, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_D3D7_SetTexture)(void*, DWORD, void*);
typedef HRESULT (WINAPI *PFN_D3D7_GetTextureStageState)(void*, DWORD, DWORD, DWORD*);
typedef HRESULT (WINAPI *PFN_D3D7_SetTextureStageState)(void*, DWORD, DWORD, DWORD);
typedef HRESULT (WINAPI *PFN_DDS7_GetSurfaceDesc)(void*, void*);
typedef HRESULT (WINAPI *PFN_DDS7_Blt)(void*, RECT*, void*, RECT*, DWORD, void*);
typedef HRESULT (WINAPI *PFN_DDS7_BltFast)(void*, DWORD, DWORD, void*, RECT*, DWORD);
typedef HRESULT (WINAPI *PFN_DDS7_Flip)(void*, void*, DWORD);

static PFN_DirectDrawCreateEx g_real_DirectDrawCreateEx;

static HMODULE g_self;
static HMODULE g_real_winmm;
static volatile LONG g_init_state; /* 0 = not started, 1 = initializing, 2 = ready */
static int g_font_enabled = 1;
static int g_font_add = 3;

static int g_trace_enabled = 0;
static DWORD g_trace_capture_ms = 2000;

/* Phase 2F: full-present-frame UI scaling + stable group identity.
 * UI quads are accumulated across every D3D scene/pass until the DirectDraw
 * presentation boundary (Flip/Blt/BltFast). Groups are then rebuilt once per
 * real frame and matched to the previous frame so each window keeps a stable
 * anchor while moving. This removes Phase 2E's scene-to-scene group collapse
 * and the resulting drag snap/jitter. */
static int g_ui_enabled = 1;
static int g_ui_scale_percent = 133;
static int g_ui_sharp_filter = 0;
static int g_ui_keep_on_screen = 1;
static DWORD g_ui_sharp_draws,g_ui_sharp_failures;
static LONG g_ui_origin_x = 0;
static LONG g_ui_origin_y = 0;
static LONG g_ui_screen_w = 3440;
static LONG g_ui_screen_h = 1440;
static int g_ui_runtime_enabled = 1;
static int g_ui_anchor_mode = 1; /* 0=OriginX/Y, 1=group edge/center, 2=screen center */
static int g_ui_group_gap = 12;
static int g_ui_match_gap = 40;
static int g_ui_stable_match_gap = 96;
static int g_ui_global_threshold_percent = 65;
static int g_ui_scale_global = 0;
static int g_ui_scale_unmatched = 0;
static int g_input_enabled = 1;
static int g_input_runtime_enabled = 1;
static DWORD g_input_max_age_ms = 250;
static DWORD g_ui_scaled_draws = 0;
static DWORD g_ui_present_serial = 0;
static DWORD g_ui_scene_serial = 0;
static DWORD g_ui_scenes_since_present = 0;
static DWORD g_ui_last_present_tick = 0;
static int g_ui_present_seen = 0;
static int g_ui_fallback_logged = 0;
static DWORD g_ui_next_stable_id = 1;
static DWORD g_ui_mapped_mouse = 0;

/* UI hit testing keeps its inverse mapping. The cursor renderer and terrain
 * ray independently sample the raw client point through the original APIs,
 * including button events and stationary-pointer frames. */
static int g_world_input_enabled = 1;
static int g_world_input_normalize = 1;
static volatile LONG g_world_raw_x;
static volatile LONG g_world_raw_y;
static volatile LONG g_world_mapped_x;
static volatile LONG g_world_mapped_y;
static DWORD g_world_input_calls;
static DWORD g_world_input_raw_uses;
static DWORD g_world_input_normalized;
static DWORD g_world_input_raw_failures;
static DWORD g_world_input_max_delta;
static LONG g_world_input_view_w;
static LONG g_world_input_view_h;
static LONG g_world_input_client_w;
static LONG g_world_input_client_h;
static int g_world_input_hook_installed;
static int g_world_input_dims_logged;

/* Cursor ACT layers are queued before their eventual D3D draw. Identify the
 * exact vertex allocation plus its immutable fields, not a rectangle shape. */
#define MAX_CURSOR_DRAWS 128
typedef struct {
    const void* verts;
    DWORD nverts, present;
    DWORD fields[4][6]; /* x/y/z/rhw/u/v; native queue may change specular */
} CursorDrawRec;
static CursorDrawRec g_cursor_draws[MAX_CURSOR_DRAWS];
static volatile LONG g_cursor_draw_lock;
static DWORD g_cursor_scope_thread;
static int g_cursor_hooks_installed;
static DWORD g_cursor_calls, g_cursor_raw_uses, g_cursor_raw_failures;
static DWORD g_cursor_submits, g_cursor_bypassed, g_cursor_overflow;
static DWORD g_cursor_expired, g_cursor_mismatched, g_cursor_peak;

/* Phase 2H: true UIWindow-owner scaling for movable windows.
 * Static analysis of this PRM build identified vtable slot 17 (offset 0x44) as
 * the per-window render method for the UIItemWnd/UIStatusWnd/UINewSkillListWnd
 * family.  We hook that method on live RTTI-validated UIWindow vtables, tag the
 * D3D7 UI quads emitted during each window render, and keep independent anchors
 * per real object.  Phase 2F geometry grouping remains as a fallback for HUD/
 * unowned UI. */
static int g_owner_scale_enabled = 1; /* Phase 2Q stable owner-submit visual matcher */
static DWORD g_owner_render_slot = 17; /* retained only for old 2H source compatibility */
static DWORD g_owner_tagged_draws = 0;
static DWORD g_owner_mapped_mouse = 0;
static DWORD g_owner_input_candidates = 0;
static DWORD g_owner_input_overlap_hits = 0;
static DWORD g_owner_input_region_peak = 0;
static DWORD g_owner_d3d_draw_order = 0;
static DWORD g_owner_input_order = 0;
static DWORD g_owner_input_manager_regions = 0;
static DWORD g_owner_input_grace_regions = 0;
static DWORD g_owner_input_manager_peak = 0;
static DWORD g_current_ui_owner = 0;
static DWORD g_current_ui_vtable = 0;

/* Phase 2Q: stable real-window submission ownership + active full-window input.
 * Phase 2P proved the full-window inverse transform works (ownerMouse > 0), but
 * only owners with a recent exact D3D match entered the input snapshot. That
 * left Inventory/Status out while Skill Tree alone qualified.
 *
 * 2Q separates input activity/z-order from deferred visual ownership. Every
 * scoped UIWindow helper call updates a monotonic input order immediately. The
 * present thread publishes any learned owner that is still present in the real
 * UIWindowMgr active lists (with a short helper-activity grace fallback). Exact
 * D3D draw order is retained only as a fresh topmost hint. ScreenToClient still
 * consumes copied rectangles/transforms only and never dereferences UIWindow. */
static int g_owner_submit_enabled = 1;
static int g_owner_tooltip_enabled = 1;
static int g_owner_all_window_calls = 1;
static DWORD g_owner_submit_tolerance = 4;
static DWORD g_owner_submit_max_age_presents = 96;
static int g_owner_input_remap_enabled = 1;
static DWORD g_owner_input_max_age_presents = 24;
static DWORD g_owner_input_exact_max_age_presents = 4;
static DWORD g_owner_submit_pos_x_off = 0x1c;
static DWORD g_owner_submit_pos_y_off = 0x20;
static DWORD g_owner_submit_pos_invalid = 0;
static DWORD g_owner_submit_pos_unreadable = 0;
static DWORD g_owner_submit_pos_range = 0;
static DWORD g_owner_submit_pos_last_obj = 0;
static LONG g_owner_submit_pos_last_x = 0;
static LONG g_owner_submit_pos_last_y = 0;
static DWORD g_owner_submit_pos_last_reason = 0;
static DWORD g_owner_submit_scoped_calls = 0;
static DWORD g_owner_submit_total_a = 0;
static DWORD g_owner_submit_total_b = 0;
static DWORD g_owner_submit_total_c = 0;
static DWORD g_owner_submit_total_matched = 0;
static DWORD g_owner_submit_total_unmatched = 0;
static DWORD g_owner_submit_total_ambiguous = 0;
static DWORD g_owner_submit_total_expired = 0;
static DWORD g_owner_submit_total_overflow = 0;
static DWORD g_owner_submit_peak_pending = 0;
static DWORD g_owner_submit_match_age_max = 0;
static DWORD g_owner_submit_newest_exact_choices = 0;
#define OWNER_AGE_HIST_BINS 128
static DWORD g_owner_submit_age_hist[OWNER_AGE_HIST_BINS]; /* bin 127 = age 127+ */
static DWORD g_owner_submit_last_expired = 0;
static DWORD g_owner_submit_last_count = 0;
static DWORD g_owner_submit_last_matched = 0;
static DWORD g_owner_submit_last_unmatched = 0;
static DWORD g_owner_submit_last_ambiguous = 0;

/* Legacy 2G stack tracer is retained in source for diagnostics but disabled in
 * the Phase 2H path. */
static int g_owner_trace_enabled = 0;
static DWORD g_owner_trace_ms = 2000;
static DWORD g_owner_scan_bytes = 4096;
static DWORD g_owner_sample_every = 4;
static DWORD g_owner_capture_until;
static DWORD g_owner_capture_serial;
static DWORD g_owner_sample_counter;
static int g_owner_capture_active;
static HMODULE g_exe;
static DWORD g_exe_size;
static volatile LONG g_trace_lock;
static DWORD g_capture_until;
static DWORD g_capture_serial;
static int g_capture_active;
static void* g_current_texture;
static DWORD g_current_tex_w;
static DWORD g_current_tex_h;
static char g_dll_path[520];
static char g_ini_path[520];
static char g_log_path[520];

/* ---------- tiny freestanding string helpers ---------- */
static unsigned int s_len(const char* s) {
    unsigned int n = 0;
    if (!s) return 0;
    while (s[n]) ++n;
    return n;
}

static char lower_ascii(char c) {
    if (c >= 'A' && c <= 'Z') return (char)(c + ('a' - 'A'));
    return c;
}

static int s_eq_ci(const char* a, const char* b) {
    unsigned int i = 0;
    if (!a || !b) return 0;
    while (a[i] && b[i]) {
        if (lower_ascii(a[i]) != lower_ascii(b[i])) return 0;
        ++i;
    }
    return a[i] == 0 && b[i] == 0;
}

static int wide_eq_ascii_ci(const WORD* w, unsigned int wchars, const char* a) {
    unsigned int i;
    if (!w || !a) return 0;
    for (i = 0; i < wchars; ++i) {
        char wc = (char)(w[i] & 0xff);
        if (!a[i] || lower_ascii(wc) != lower_ascii(a[i])) return 0;
    }
    return a[wchars] == 0;
}

static void s_copy(char* dst, unsigned int cap, const char* src) {
    unsigned int i = 0;
    if (!cap) return;
    while (src && src[i] && i + 1 < cap) { dst[i] = src[i]; ++i; }
    dst[i] = 0;
}

static void s_append(char* dst, unsigned int cap, const char* src) {
    unsigned int n = s_len(dst), i = 0;
    if (n >= cap) return;
    while (src && src[i] && n + i + 1 < cap) { dst[n+i] = src[i]; ++i; }
    dst[n+i] = 0;
}


static void s_append_hex8(char* dst, unsigned int cap, DWORD v) {
    static const char hex[] = "0123456789ABCDEF";
    unsigned int n = s_len(dst), i;
    if (n + 10 >= cap) return;
    dst[n++] = '0'; dst[n++] = 'x';
    for (i = 0; i < 8; ++i) dst[n++] = hex[(v >> ((7-i)*4)) & 0xf];
    dst[n] = 0;
}

static void s_append_uint(char* dst, unsigned int cap, DWORD v) {
    char tmp[16]; unsigned int n=0, i;
    if (v == 0) tmp[n++]='0';
    else while (v && n < sizeof(tmp)) { tmp[n++] = (char)('0' + (v%10)); v/=10; }
    for (i=0; i<n; ++i) {
        unsigned int d=s_len(dst); if (d+1>=cap) break;
        dst[d]=tmp[n-1-i]; dst[d+1]=0;
    }
}

static void s_append_int(char* dst, unsigned int cap, LONG v) {
    char t[16]; unsigned int n=0; DWORD u;
    if(v<0) { s_append(dst,cap,"-"); u=(DWORD)(-(v+1))+1; } else u=(DWORD)v;
    do { t[n++]=(char)('0'+(u%10)); u/=10; } while(u && n<sizeof(t));
    while(n) { char c[2]; c[0]=t[--n]; c[1]=0; s_append(dst,cap,c); }
}

static int guid_eq(const GUID* a, DWORD d1, WORD d2, WORD d3, const BYTE d4[8]) {
    unsigned int i;
    if (!a || a->Data1 != d1 || a->Data2 != d2 || a->Data3 != d3) return 0;
    for (i=0;i<8;++i) if (a->Data4[i] != d4[i]) return 0;
    return 1;
}

/* ---------- PEB module walking + PE export resolver ---------- */
static void* get_peb(void) {
    void* p;
    __asm__ volatile ("movl %%fs:0x30, %0" : "=r"(p));
    return p;
}

static HMODULE find_loaded_module(const char* wanted) {
    BYTE* peb = (BYTE*)get_peb();
    BYTE* ldr;
    BYTE* head;
    BYTE* link;
    if (!peb) return 0;
    ldr = *(BYTE**)(peb + 0x0c);
    if (!ldr) return 0;
    head = ldr + 0x0c; /* InLoadOrderModuleList */
    link = *(BYTE**)head;
    while (link && link != head) {
        BYTE* entry = link; /* InLoadOrderLinks is first field */
        HMODULE base = *(HMODULE*)(entry + 0x18);
        WORD name_len_bytes = *(WORD*)(entry + 0x2c);
        WORD* name_buf = *(WORD**)(entry + 0x30);
        if (name_buf && wide_eq_ascii_ci(name_buf, (unsigned int)(name_len_bytes / 2), wanted)) return base;
        link = *(BYTE**)link;
    }
    return 0;
}

static void* resolve_export(HMODULE module, const char* name);

static void* resolve_forwarder(const char* fwd) {
    char mod[80];
    char fun[128];
    unsigned int i = 0, j = 0;
    HMODULE m;
    while (fwd[i] && fwd[i] != '.' && i + 1 < sizeof(mod)) { mod[i] = fwd[i]; ++i; }
    mod[i] = 0;
    if (fwd[i] != '.') return 0;
    ++i;
    while (fwd[i] && j + 1 < sizeof(fun)) { fun[j++] = fwd[i++]; }
    fun[j] = 0;
    if (!mod[0] || !fun[0] || fun[0] == '#') return 0;
    if (s_len(mod) + 4 < sizeof(mod) && !(s_len(mod) >= 4 && lower_ascii(mod[s_len(mod)-4]) == '.')) s_append(mod, sizeof(mod), ".dll");
    m = find_loaded_module(mod);
    if (!m) return 0;
    return resolve_export(m, fun);
}

static void* resolve_export(HMODULE module, const char* name) {
    BYTE* base = (BYTE*)module;
    DWORD peoff, exprva, expsz;
    BYTE* opt;
    BYTE* exp;
    DWORD n_names, funcs_rva, names_rva, ords_rva;
    DWORD* funcs;
    DWORD* names;
    WORD* ords;
    DWORD i;
    if (!base || *(WORD*)base != 0x5a4d) return 0;
    peoff = *(DWORD*)(base + 0x3c);
    if (*(DWORD*)(base + peoff) != 0x00004550UL) return 0;
    opt = base + peoff + 24;
    if (*(WORD*)opt != 0x10b) return 0;
    exprva = *(DWORD*)(opt + 96);
    expsz  = *(DWORD*)(opt + 100);
    if (!exprva) return 0;
    exp = base + exprva;
    n_names   = *(DWORD*)(exp + 24);
    funcs_rva = *(DWORD*)(exp + 28);
    names_rva = *(DWORD*)(exp + 32);
    ords_rva  = *(DWORD*)(exp + 36);
    funcs = (DWORD*)(base + funcs_rva);
    names = (DWORD*)(base + names_rva);
    ords  = (WORD*)(base + ords_rva);
    for (i = 0; i < n_names; ++i) {
        const char* n = (const char*)(base + names[i]);
        if (s_eq_ci(n, name)) {
            DWORD rva = funcs[ords[i]];
            if (rva >= exprva && rva < exprva + expsz) return resolve_forwarder((const char*)(base + rva));
            return base + rva;
        }
    }
    return 0;
}

static void bootstrap_kernel32(void) {
    HMODULE k32 = find_loaded_module("kernel32.dll");
    if (!k32) return;
    g_LoadLibraryA = (PFN_LoadLibraryA)resolve_export(k32, "LoadLibraryA");
    g_GetSystemDirectoryA = (PFN_GetSystemDirectoryA)resolve_export(k32, "GetSystemDirectoryA");
    g_VirtualProtect = (PFN_VirtualProtect)resolve_export(k32, "VirtualProtect");
    g_FlushInstructionCache = (PFN_FlushInstructionCache)resolve_export(k32, "FlushInstructionCache");
    g_VirtualQuery = (PFN_VirtualQuery)resolve_export(k32, "VirtualQuery");
    g_GetModuleHandleA = (PFN_GetModuleHandleA)resolve_export(k32, "GetModuleHandleA");
    g_GetModuleFileNameA = (PFN_GetModuleFileNameA)resolve_export(k32, "GetModuleFileNameA");
    g_GetPrivateProfileIntA = (PFN_GetPrivateProfileIntA)resolve_export(k32, "GetPrivateProfileIntA");
    g_CreateFileA = (PFN_CreateFileA)resolve_export(k32, "CreateFileA");
    g_WriteFile = (PFN_WriteFile)resolve_export(k32, "WriteFile");
    g_SetFilePointer = (PFN_SetFilePointer)resolve_export(k32, "SetFilePointer");
    g_CloseHandle = (PFN_CloseHandle)resolve_export(k32, "CloseHandle");
    g_GetTickCount = (PFN_GetTickCount)resolve_export(k32, "GetTickCount");
    g_GetCurrentThreadId = (PFN_GetCurrentThreadId)resolve_export(k32, "GetCurrentThreadId");
    g_DisableThreadLibraryCalls = (PFN_DisableThreadLibraryCalls)resolve_export(k32, "DisableThreadLibraryCalls");
    {
        HMODULE u32 = find_loaded_module("user32.dll");
        HMODULE nt = find_loaded_module("ntdll.dll");
        if (u32) g_GetAsyncKeyState = (PFN_GetAsyncKeyState)resolve_export(u32, "GetAsyncKeyState");
        if (nt) g_RtlCaptureStackBackTrace = (PFN_RtlCaptureStackBackTrace)resolve_export(nt, "RtlCaptureStackBackTrace");
    }
}

/* ---------- paths + logging ---------- */
static void make_sidecar_path(char* out, unsigned int cap, const char* file) {
    unsigned int i, n;
    s_copy(out, cap, g_dll_path);
    n = s_len(out);
    for (i = n; i > 0; --i) {
        if (out[i-1] == '\\' || out[i-1] == '/') { out[i] = 0; break; }
    }
    if (i == 0) out[0] = 0;
    s_append(out, cap, file);
}

static void init_paths(void) {
    if (g_GetModuleFileNameA) g_GetModuleFileNameA(g_self, g_dll_path, sizeof(g_dll_path));
    make_sidecar_path(g_ini_path, sizeof(g_ini_path), "prm-ui-fix.ini");
    make_sidecar_path(g_log_path, sizeof(g_log_path), "prm-ui-fix.log");
}

static void log_raw(const char* s) {
    HANDLE h;
    DWORD wrote = 0;
    if (!g_CreateFileA || !g_WriteFile || !g_CloseHandle || !g_log_path[0]) return;
    h = g_CreateFileA(g_log_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0);
    if (h == INVALID_HANDLE_VALUE) return;
    g_WriteFile(h, s, (DWORD)s_len(s), &wrote, 0);
    g_CloseHandle(h);
}

static void log_line(const char* s) {
    log_raw(s); log_raw("\r\n");
}

static void log_uint(const char* label, DWORD v) {
    char buf[64];
    char num[16];
    unsigned int pos = 0, i;
    if (v == 0) num[pos++] = '0';
    else {
        while (v && pos < sizeof(num)-1) { num[pos++] = (char)('0' + (v % 10)); v /= 10; }
    }
    s_copy(buf, sizeof(buf), label);
    for (i = 0; i < pos; ++i) {
        unsigned int n = s_len(buf);
        if (n + 1 < sizeof(buf)) { buf[n] = num[pos-1-i]; buf[n+1] = 0; }
    }
    log_line(buf);
}

static void log_hex(const char* label, DWORD v) {
    static const char hex[] = "0123456789ABCDEF";
    char buf[64];
    unsigned int n, i;
    s_copy(buf, sizeof(buf), label);
    s_append(buf, sizeof(buf), "0x");
    n = s_len(buf);
    for (i = 0; i < 8 && n + i + 1 < sizeof(buf); ++i) buf[n+i] = hex[(v >> ((7-i)*4)) & 0xf];
    buf[n+i] = 0;
    log_line(buf);
}

/* ---------- executable identification ---------- */
static DWORD hash_text_section(HMODULE module, DWORD* out_timestamp, DWORD* out_image_size) {
    BYTE* base = (BYTE*)module;
    DWORD peoff, nsects, optsz, i;
    BYTE* coff;
    BYTE* opt;
    BYTE* sec;
    DWORD hash = 2166136261UL;
    if (!base || *(WORD*)base != 0x5a4d) return 0;
    peoff = *(DWORD*)(base + 0x3c);
    if (*(DWORD*)(base + peoff) != 0x00004550UL) return 0;
    coff = base + peoff + 4;
    nsects = *(WORD*)(coff + 2);
    if (out_timestamp) *out_timestamp = *(DWORD*)(coff + 4);
    optsz = *(WORD*)(coff + 16);
    opt = coff + 20;
    if (out_image_size) *out_image_size = *(DWORD*)(opt + 56);
    sec = opt + optsz;
    for (i = 0; i < nsects; ++i, sec += 40) {
        if (sec[0]=='.' && sec[1]=='t' && sec[2]=='e' && sec[3]=='x' && sec[4]=='t') {
            DWORD vsize = *(DWORD*)(sec + 8);
            DWORD rva = *(DWORD*)(sec + 12);
            DWORD j;
            BYTE* p = base + rva;
            for (j = 0; j < vsize; ++j) { hash ^= p[j]; hash *= 16777619UL; }
            return hash;
        }
    }
    return 0;
}

/* ---------- IAT hook ---------- */
static int patch_import(HMODULE module, const char* dll_name, const char* func_name, void* hook, void** original) {
    BYTE* base = (BYTE*)module;
    DWORD peoff, imprva;
    BYTE* opt;
    BYTE* desc;
    if (!base || !g_VirtualProtect) return 0;
    peoff = *(DWORD*)(base + 0x3c);
    opt = base + peoff + 24;
    if (*(WORD*)opt != 0x10b) return 0;
    imprva = *(DWORD*)(opt + 104); /* DataDirectory[IMPORT].VirtualAddress */
    if (!imprva) return 0;
    desc = base + imprva;
    while (*(DWORD*)(desc + 12)) {
        const char* dname = (const char*)(base + *(DWORD*)(desc + 12));
        if (s_eq_ci(dname, dll_name)) {
            DWORD oft = *(DWORD*)(desc + 0);
            DWORD ft  = *(DWORD*)(desc + 16);
            DWORD idx = 0;
            if (!oft) oft = ft;
            while (*(DWORD*)(base + oft + idx*4)) {
                DWORD thunk = *(DWORD*)(base + oft + idx*4);
                if (!(thunk & 0x80000000UL)) {
                    const char* iname = (const char*)(base + thunk + 2);
                    if (s_eq_ci(iname, func_name)) {
                        void** slot = (void**)(base + ft + idx*4);
                        DWORD oldp = 0, tmp = 0;
                        if (original) *original = *slot;
                        if (!g_VirtualProtect(slot, 4, PAGE_READWRITE, &oldp)) return 0;
                        *slot = hook;
                        g_VirtualProtect(slot, 4, oldp, &tmp);
                        return 1;
                    }
                }
                ++idx;
            }
            return 0;
        }
        desc += 20;
    }
    return 0;
}

static int adjusted_height(int h) {
    if (!g_font_enabled || g_font_add == 0 || h == 0) return h;
    if (h < 0) return h - g_font_add;
    return h + g_font_add;
}

static HFONT WINAPI hook_CreateFontA(int h,int w,int esc,int ori,int weight,DWORD italic,DWORD underline,DWORD strike,DWORD charset,DWORD outp,DWORD clipp,DWORD quality,DWORD pitch,LPCSTR face) {
    if (!g_real_CreateFontA) return 0;
    return g_real_CreateFontA(adjusted_height(h),w,esc,ori,weight,italic,underline,strike,charset,outp,clipp,quality,pitch,face);
}

static HFONT WINAPI hook_CreateFontIndirectA(const LOGFONTA* in) {
    LOGFONTA copy;
    unsigned int i;
    if (!g_real_CreateFontIndirectA || !in) return 0;
    /* byte copy avoids CRT memcpy */
    for (i = 0; i < sizeof(LOGFONTA); ++i) ((BYTE*)&copy)[i] = ((const BYTE*)in)[i];
    copy.lfHeight = adjusted_height(copy.lfHeight);
    return g_real_CreateFontIndirectA(&copy);
}

static void install_font_hooks(void) {
    HMODULE exe = g_GetModuleHandleA ? g_GetModuleHandleA(0) : 0;
    int a = 0, b = 0;
    if (!exe) { log_line("Font hooks: main module not found"); return; }
    a = patch_import(exe, "GDI32.dll", "CreateFontA", (void*)hook_CreateFontA, (void**)&g_real_CreateFontA);
    b = patch_import(exe, "GDI32.dll", "CreateFontIndirectA", (void*)hook_CreateFontIndirectA, (void**)&g_real_CreateFontIndirectA);
    log_line(a ? "CreateFontA IAT hook: OK" : "CreateFontA IAT hook: NOT FOUND");
    log_line(b ? "CreateFontIndirectA IAT hook: OK" : "CreateFontIndirectA IAT hook: NOT FOUND");
}


/* ---------- Phase 2 Direct3D7 callsite tracer ---------- */
#define MAX_VT_HOOKS 8
#define MAX_DRAW_STATS 512
#define MAX_STACK_FRAMES 8

typedef struct {
    void** vt;
    void* orig_qi;
} DD7HookRec;

typedef struct {
    void** vt;
    void* orig_create_device;
} D3D7HookRec;

typedef struct {
    void** vt;
    void* orig_begin_scene;
    void* orig_end_scene;
    void* orig_draw;
    void* orig_draw_indexed;
    void* orig_draw_strided;
    void* orig_draw_indexed_strided;
    void* orig_draw_vb;
    void* orig_draw_indexed_vb;
    void* orig_set_texture;
} DevHookRec;

typedef struct {
    void** vt;
    void* orig_blt;
    void* orig_bltfast;
    void* orig_flip;
} SurfHookRec;

typedef struct {
    DWORD caller_rva;
    DWORD method; /* 0=DP 1=DIP 2=DPS 3=DIPS 4=DPVB 5=DIPVB */
    DWORD prim_type;
    DWORD fvf;
    DWORD calls;
    DWORD total_vertices;
    DWORD min_vertices;
    DWORD max_vertices;
    DWORD tex_w;
    DWORD tex_h;
    LONG min_x, max_x, min_y, max_y;
    LONG min_z1000, max_z1000;
    LONG min_rhw1000, max_rhw1000;
    DWORD sampled_vertices;
    DWORD stack[MAX_STACK_FRAMES];
} DrawStat;

static DD7HookRec g_dd7_hooks[MAX_VT_HOOKS];
static D3D7HookRec g_d3d7_hooks[MAX_VT_HOOKS];
static DevHookRec g_dev_hooks[MAX_VT_HOOKS];
static SurfHookRec g_surf_hooks[MAX_VT_HOOKS];
static void* g_render_targets[MAX_VT_HOOKS];
static DWORD g_render_target_count;
static DrawStat g_draw_stats[MAX_DRAW_STATS];
static DWORD g_draw_stat_count;

static DWORD ptr_to_rva(void* p) {
    ULONG_PTR a=(ULONG_PTR)p, b=(ULONG_PTR)g_exe;
    if (g_exe && a >= b && a < b + g_exe_size) return (DWORD)(a-b);
    return 0xffffffffUL;
}

static void trace_lock(void) {
    while (__atomic_exchange_n(&g_trace_lock, 1, __ATOMIC_ACQUIRE)) __asm__ volatile("pause");
}
static void trace_unlock(void) { __atomic_store_n(&g_trace_lock, 0, __ATOMIC_RELEASE); }

static int patch_vtable_slot(void** vt, DWORD index, void* hook, void** original) {
    void** slot; DWORD oldp=0,tmp=0;
    if (!vt || !g_VirtualProtect) return 0;
    slot=vt+index;
    if (*slot == hook) return 1;
    if (original) *original=*slot;
    if (!g_VirtualProtect(slot,4,PAGE_READWRITE,&oldp)) return 0;
    *slot=hook;
    g_VirtualProtect(slot,4,oldp,&tmp);
    return 1;
}

static DD7HookRec* dd7_rec(void* self) {
    void** vt = self ? *(void***)self : 0; DWORD i;
    for(i=0;i<MAX_VT_HOOKS;++i) if(g_dd7_hooks[i].vt==vt) return &g_dd7_hooks[i];
    return 0;
}
static D3D7HookRec* d3d7_rec(void* self) {
    void** vt = self ? *(void***)self : 0; DWORD i;
    for(i=0;i<MAX_VT_HOOKS;++i) if(g_d3d7_hooks[i].vt==vt) return &g_d3d7_hooks[i];
    return 0;
}
static DevHookRec* dev_rec(void* self) {
    void** vt = self ? *(void***)self : 0; DWORD i;
    for(i=0;i<MAX_VT_HOOKS;++i) if(g_dev_hooks[i].vt==vt) return &g_dev_hooks[i];
    return 0;
}
static SurfHookRec* surf_rec(void* self) {
    void** vt = self ? *(void***)self : 0; DWORD i;
    for(i=0;i<MAX_VT_HOOKS;++i) if(g_surf_hooks[i].vt==vt) return &g_surf_hooks[i];
    return 0;
}

static int is_render_target(void* s) {
    DWORD i;
    for(i=0;i<g_render_target_count;++i) if(g_render_targets[i]==s) return 1;
    return 0;
}

static void remember_render_target(void* s) {
    DWORD i; if(!s) return;
    for(i=0;i<g_render_target_count;++i) if(g_render_targets[i]==s) return;
    if(g_render_target_count<MAX_VT_HOOKS) g_render_targets[g_render_target_count++]=s;
}

static HRESULT WINAPI hook_DD7_QueryInterface(void* self, const GUID* iid, void** out);
static HRESULT WINAPI hook_D3D7_CreateDevice(void* self, const GUID* clsid, void* target, void** out);
static HRESULT WINAPI hook_BeginScene(void* self);
static HRESULT WINAPI hook_EndScene(void* self);
static HRESULT WINAPI hook_DrawPrimitive(void* self, DWORD prim, DWORD fvf, const void* verts, DWORD nverts, DWORD flags);
static HRESULT WINAPI hook_DrawIndexedPrimitive(void* self, DWORD prim, DWORD fvf, const void* verts, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags);
static HRESULT WINAPI hook_DrawPrimitiveStrided(void* self, DWORD prim, DWORD fvf, const void* data, DWORD nverts, DWORD flags);
static HRESULT WINAPI hook_DrawIndexedPrimitiveStrided(void* self, DWORD prim, DWORD fvf, const void* data, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags);
static HRESULT WINAPI hook_DrawPrimitiveVB(void* self, DWORD prim, void* vb, DWORD start, DWORD nverts, DWORD flags);
static HRESULT WINAPI hook_DrawIndexedPrimitiveVB(void* self, DWORD prim, void* vb, DWORD start, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags);
static HRESULT WINAPI hook_SetTexture(void* self, DWORD stage, void* tex);
static HRESULT WINAPI hook_SurfaceBlt(void* self, RECT* dst, void* src, RECT* srcRect, DWORD flags, void* fx);
static HRESULT WINAPI hook_SurfaceBltFast(void* self, DWORD x, DWORD y, void* src, RECT* srcRect, DWORD flags);
static HRESULT WINAPI hook_SurfaceFlip(void* self, void* targetOverride, DWORD flags);

static void install_dd7_hooks(void* obj) {
    void** vt; DWORD i; DD7HookRec* r=0;
    if(!obj) return; vt=*(void***)obj;
    for(i=0;i<MAX_VT_HOOKS;++i) { if(g_dd7_hooks[i].vt==vt) return; if(!g_dd7_hooks[i].vt && !r) r=&g_dd7_hooks[i]; }
    if(!r) return; r->vt=vt;
    if(patch_vtable_slot(vt,0,(void*)hook_DD7_QueryInterface,&r->orig_qi)) log_line("DirectDraw7 QueryInterface hook: OK");
    else { r->vt=0; log_line("DirectDraw7 QueryInterface hook: FAILED"); }
}

static void install_d3d7_hooks(void* obj) {
    void** vt; DWORD i; D3D7HookRec* r=0;
    if(!obj) return; vt=*(void***)obj;
    for(i=0;i<MAX_VT_HOOKS;++i) { if(g_d3d7_hooks[i].vt==vt) return; if(!g_d3d7_hooks[i].vt && !r) r=&g_d3d7_hooks[i]; }
    if(!r) return; r->vt=vt;
    /* IDirect3D7::CreateDevice is vtable slot 4. */
    if(patch_vtable_slot(vt,4,(void*)hook_D3D7_CreateDevice,&r->orig_create_device)) log_line("Direct3D7 CreateDevice hook: OK");
    else { r->vt=0; log_line("Direct3D7 CreateDevice hook: FAILED"); }
}

static void install_surface_hooks(void* obj) {
    void** vt; DWORD i; SurfHookRec* r=0; int a,b,c;
    if(!obj) return; vt=*(void***)obj;
    for(i=0;i<MAX_VT_HOOKS;++i) { if(g_surf_hooks[i].vt==vt) return; if(!g_surf_hooks[i].vt && !r) r=&g_surf_hooks[i]; }
    if(!r) return; r->vt=vt;
    /* IDirectDrawSurface7: Blt=5, BltFast=7, Flip=11. */
    a=patch_vtable_slot(vt,5,(void*)hook_SurfaceBlt,&r->orig_blt);
    b=patch_vtable_slot(vt,7,(void*)hook_SurfaceBltFast,&r->orig_bltfast);
    c=patch_vtable_slot(vt,11,(void*)hook_SurfaceFlip,&r->orig_flip);
    if(a&&b&&c) log_line("DirectDrawSurface7 present hooks: OK (Blt/BltFast/Flip)");
    else log_line("DirectDrawSurface7 present hooks: PARTIAL/FAILED");
}

static void install_device_hooks(void* obj) {
    void** vt; DWORD i; DevHookRec* r=0; int a,b,c,d,e,f,g,h,j;
    if(!obj) return; vt=*(void***)obj;
    for(i=0;i<MAX_VT_HOOKS;++i) { if(g_dev_hooks[i].vt==vt) return; if(!g_dev_hooks[i].vt && !r) r=&g_dev_hooks[i]; }
    if(!r) return; r->vt=vt;
    /* IDirect3DDevice7: BeginScene=5, EndScene=6, draw family=25,26,29,30,31,32; SetTexture=35. */
    h=patch_vtable_slot(vt,5,(void*)hook_BeginScene,&r->orig_begin_scene);
    j=patch_vtable_slot(vt,6,(void*)hook_EndScene,&r->orig_end_scene);
    a=patch_vtable_slot(vt,25,(void*)hook_DrawPrimitive,&r->orig_draw);
    b=patch_vtable_slot(vt,26,(void*)hook_DrawIndexedPrimitive,&r->orig_draw_indexed);
    c=patch_vtable_slot(vt,29,(void*)hook_DrawPrimitiveStrided,&r->orig_draw_strided);
    d=patch_vtable_slot(vt,30,(void*)hook_DrawIndexedPrimitiveStrided,&r->orig_draw_indexed_strided);
    e=patch_vtable_slot(vt,31,(void*)hook_DrawPrimitiveVB,&r->orig_draw_vb);
    f=patch_vtable_slot(vt,32,(void*)hook_DrawIndexedPrimitiveVB,&r->orig_draw_indexed_vb);
    g=patch_vtable_slot(vt,35,(void*)hook_SetTexture,&r->orig_set_texture);
    if(a&&b&&c&&d&&e&&f&&g&&h&&j) log_line("Direct3DDevice7 hooks: OK (Phase 3B owner UI + isolated world input)");
    else log_line("Direct3DDevice7 hooks: PARTIAL/FAILED");
}

static void capture_texture_desc(void* tex) {
    BYTE desc[124]; unsigned int i; void** vt; PFN_DDS7_GetSurfaceDesc fn;
    g_current_tex_w=0; g_current_tex_h=0;
    if(!tex) return;
    for(i=0;i<sizeof(desc);++i) desc[i]=0;
    *(DWORD*)(desc+0)=124;
    vt=*(void***)tex; if(!vt) return;
    fn=(PFN_DDS7_GetSurfaceDesc)vt[22]; /* IDirectDrawSurface7::GetSurfaceDesc */
    if(fn && fn(tex,desc)>=0) { g_current_tex_h=*(DWORD*)(desc+8); g_current_tex_w=*(DWORD*)(desc+12); }
}

static LONG f_to_i1000(float v) {
    float x=v*1000.0f;
    if(x>2147483000.0f) return 2147483000L;
    if(x<-2147483000.0f) return -2147483000L;
    return (LONG)(x>=0.0f ? x+0.5f : x-0.5f);
}

static LONG f_to_i(float v) {
    if(v>2147483000.0f) return 2147483000L;
    if(v<-2147483000.0f) return -2147483000L;
    return (LONG)(v>=0.0f ? v+0.5f : v-0.5f);
}

static DWORD fvf_stride(DWORD fvf) {
    DWORD n=0, tc;
    if((fvf & 0x000eUL)==0x0004UL) n+=16; /* XYZRHW */
    else if((fvf & 0x000eUL)==0x0002UL) n+=12; /* XYZ */
    if(fvf & 0x0010UL) n+=12; /* normal */
    if(fvf & 0x0040UL) n+=4;  /* diffuse */
    if(fvf & 0x0080UL) n+=4;  /* specular */
    tc=(fvf>>8)&0x0fUL;
    n += tc*8; /* good for this client's FVF 0x1c4 / 0x2c4 */
    return n;
}

static void capture_ebp_chain(void* frame, DWORD out[MAX_STACK_FRAMES]) {
    DWORD i;
    ULONG_PTR base=(ULONG_PTR)g_exe, limit=base+g_exe_size;
    ULONG_PTR* fp=(ULONG_PTR*)frame;
    for(i=0;i<MAX_STACK_FRAMES;++i) out[i]=0xffffffffUL;
    for(i=0;i<MAX_STACK_FRAMES && fp;++i) {
        ULONG_PTR ret, next;
        ret=fp[1];
        if(ret>=base && ret<limit) out[i]=(DWORD)(ret-base);
        next=fp[0];
        if(!next || next<=(ULONG_PTR)fp || next-(ULONG_PTR)fp>0x200000UL || (next&3)) break;
        fp=(ULONG_PTR*)next;
    }
}

static void sample_vertices(DrawStat* st, DWORD fvf, const void* verts, DWORD nverts) {
    DWORD stride,i,limit;
    const BYTE* p=(const BYTE*)verts;
    if(!st || !p || !nverts || (fvf & 0x000eUL)!=0x0004UL) return;
    stride=fvf_stride(fvf); if(stride<16 || stride>128) return;
    limit=nverts; if(limit>256) limit=256;
    for(i=0;i<limit;++i) {
        const float* v=(const float*)(p+i*stride);
        LONG x=f_to_i(v[0]), y=f_to_i(v[1]), z=f_to_i1000(v[2]), rhw=f_to_i1000(v[3]);
        if(!st->sampled_vertices) {
            st->min_x=st->max_x=x; st->min_y=st->max_y=y;
            st->min_z1000=st->max_z1000=z; st->min_rhw1000=st->max_rhw1000=rhw;
        } else {
            if(x<st->min_x)st->min_x=x; if(x>st->max_x)st->max_x=x;
            if(y<st->min_y)st->min_y=y; if(y>st->max_y)st->max_y=y;
            if(z<st->min_z1000)st->min_z1000=z; if(z>st->max_z1000)st->max_z1000=z;
            if(rhw<st->min_rhw1000)st->min_rhw1000=rhw; if(rhw>st->max_rhw1000)st->max_rhw1000=rhw;
        }
        ++st->sampled_vertices;
    }
}

static void reset_draw_stats(void) {
    DWORD i,j; g_draw_stat_count=0;
    for(i=0;i<MAX_DRAW_STATS;++i) {
        g_draw_stats[i].calls=0; g_draw_stats[i].caller_rva=0; g_draw_stats[i].sampled_vertices=0;
        for(j=0;j<MAX_STACK_FRAMES;++j) g_draw_stats[i].stack[j]=0xffffffffUL;
    }
}

static void maybe_start_capture(void) {
    short k;
    if(!g_trace_enabled || !g_GetAsyncKeyState || !g_GetTickCount) return;
    k=g_GetAsyncKeyState(VK_TRACE_CAPTURE);
    if((k & 1) && !g_capture_active) {
        trace_lock(); reset_draw_stats(); g_capture_active=1; ++g_capture_serial;
        g_capture_until=g_GetTickCount()+g_trace_capture_ms; trace_unlock();
        log_line("--- UI TRACE CAPTURE START (F4) ---");
    }
}

static void log_draw_stat(const DrawStat* st, DWORD rank) {
    char b[512]; DWORD i;
    b[0]=0; s_append(b,sizeof(b),"#"); s_append_uint(b,sizeof(b),rank);
    s_append(b,sizeof(b)," caller="); s_append_hex8(b,sizeof(b),st->caller_rva);
    if(st->method==0) s_append(b,sizeof(b)," DP");
    else if(st->method==1) s_append(b,sizeof(b)," DIP");
    else if(st->method==2) s_append(b,sizeof(b)," DPS");
    else if(st->method==3) s_append(b,sizeof(b)," DIPS");
    else if(st->method==4) s_append(b,sizeof(b)," DPVB");
    else if(st->method==5) s_append(b,sizeof(b)," DIPVB");
    else s_append(b,sizeof(b)," DRAW");
    s_append(b,sizeof(b)," prim="); s_append_uint(b,sizeof(b),st->prim_type);
    s_append(b,sizeof(b)," fvf="); s_append_hex8(b,sizeof(b),st->fvf);
    s_append(b,sizeof(b)," calls="); s_append_uint(b,sizeof(b),st->calls);
    s_append(b,sizeof(b)," verts="); s_append_uint(b,sizeof(b),st->total_vertices);
    s_append(b,sizeof(b)," min/max="); s_append_uint(b,sizeof(b),st->min_vertices); s_append(b,sizeof(b),"/"); s_append_uint(b,sizeof(b),st->max_vertices);
    s_append(b,sizeof(b)," tex="); s_append_uint(b,sizeof(b),st->tex_w); s_append(b,sizeof(b),"x"); s_append_uint(b,sizeof(b),st->tex_h);
    if(st->sampled_vertices) {
        s_append(b,sizeof(b)," xy="); s_append_int(b,sizeof(b),st->min_x); s_append(b,sizeof(b),","); s_append_int(b,sizeof(b),st->min_y);
        s_append(b,sizeof(b),".."); s_append_int(b,sizeof(b),st->max_x); s_append(b,sizeof(b),","); s_append_int(b,sizeof(b),st->max_y);
        s_append(b,sizeof(b)," z1000="); s_append_int(b,sizeof(b),st->min_z1000); s_append(b,sizeof(b),".."); s_append_int(b,sizeof(b),st->max_z1000);
        s_append(b,sizeof(b)," rhw1000="); s_append_int(b,sizeof(b),st->min_rhw1000); s_append(b,sizeof(b),".."); s_append_int(b,sizeof(b),st->max_rhw1000);
    }
    s_append(b,sizeof(b)," stack=");
    for(i=0;i<MAX_STACK_FRAMES;++i) { if(i) s_append(b,sizeof(b),","); s_append_hex8(b,sizeof(b),st->stack[i]); }
    log_line(b);
}

static void dump_capture(void) {
    DWORD rank, used[MAX_DRAW_STATS], n=g_draw_stat_count, i,j,best;
    char hdr[128];
    if(n>MAX_DRAW_STATS) n=MAX_DRAW_STATS;
    for(i=0;i<n;++i) used[i]=0;
    hdr[0]=0; s_append(hdr,sizeof(hdr),"--- UI TRACE CAPTURE END #"); s_append_uint(hdr,sizeof(hdr),g_capture_serial);
    s_append(hdr,sizeof(hdr)," entries="); s_append_uint(hdr,sizeof(hdr),n); s_append(hdr,sizeof(hdr)," ---"); log_line(hdr);
    for(rank=1; rank<=n; ++rank) {
        best=0xffffffffUL;
        for(j=0;j<n;++j) if(!used[j] && (best==0xffffffffUL || g_draw_stats[j].calls>g_draw_stats[best].calls)) best=j;
        if(best==0xffffffffUL) break; used[best]=1; log_draw_stat(&g_draw_stats[best],rank);
    }
    log_line("--- END UI TRACE ---");
}

static void maybe_finish_capture(void) {
    if(!g_capture_active || !g_GetTickCount) return;
    if((LONG)(g_GetTickCount()-g_capture_until) >= 0) {
        trace_lock();
        if(g_capture_active) { g_capture_active=0; trace_unlock(); dump_capture(); }
        else trace_unlock();
    }
}

static void add_draw_stat(DWORD method, DWORD prim, DWORD fvf, DWORD nverts, const void* verts, void* ret, void* frame) {
    DWORD caller=ptr_to_rva(ret), i; DrawStat* st=0;
    if(!g_capture_active) return;
    trace_lock();
    for(i=0;i<g_draw_stat_count;++i) {
        DrawStat* x=&g_draw_stats[i];
        if(x->caller_rva==caller && x->method==method && x->prim_type==prim && x->fvf==fvf && x->tex_w==g_current_tex_w && x->tex_h==g_current_tex_h) { st=x; break; }
    }
    if(!st && g_draw_stat_count<MAX_DRAW_STATS) {
        st=&g_draw_stats[g_draw_stat_count++];
        st->caller_rva=caller; st->method=method; st->prim_type=prim; st->fvf=fvf; st->calls=0; st->total_vertices=0;
        st->min_vertices=nverts; st->max_vertices=nverts; st->tex_w=g_current_tex_w; st->tex_h=g_current_tex_h;
        for(i=0;i<MAX_STACK_FRAMES;++i) st->stack[i]=0xffffffffUL;
        capture_ebp_chain(frame,st->stack);
        st->sampled_vertices=0;
    }
    if(st) { ++st->calls; st->total_vertices+=nverts; if(nverts<st->min_vertices)st->min_vertices=nverts; if(nverts>st->max_vertices)st->max_vertices=nverts; sample_vertices(st,fvf,verts,nverts); }
    trace_unlock();
}



/* ---------- Phase 2G stable UI baseline + RTTI ownership tracing ---------- */
static float ui_scale_factor(void) { return ((float)g_ui_scale_percent) * 0.01f; }
static float f_abs(float x) { return x < 0.0f ? -x : x; }

#define MAX_UI_FRAME_RECTS 1024
#define MAX_UI_GROUPS 128

typedef struct { float l,t,r,b; } UIRectF;
typedef struct {
    float l,t,r,b;
    float ax,ay;
    int is_global;
    DWORD stable_id;
} UIGroup;
typedef struct {
    UIRectF rect;
    WORD group_index;
} UIGroupMember;

static UIRectF g_ui_frame_rects[MAX_UI_FRAME_RECTS];
static DWORD g_ui_frame_rect_hints[MAX_UI_FRAME_RECTS];
static DWORD g_ui_frame_rect_count;
static UIGroup g_ui_prev_groups[MAX_UI_GROUPS];
static DWORD g_ui_prev_group_count;
static UIGroupMember g_ui_prev_members[MAX_UI_FRAME_RECTS];
static DWORD g_ui_prev_member_count;
static volatile LONG g_ui_group_lock;
static volatile LONG g_owner_input_region_lock;
static DWORD g_ui_group_generation;
static UIGroup g_ui_build_groups[MAX_UI_GROUPS];
static UIGroupMember g_ui_build_members[MAX_UI_FRAME_RECTS];

/* ---------- Phase 2G RTTI UI ownership tracing ---------- */
#define MAX_OWNER_STATS 192

typedef struct {
    DWORD object_ptr;
    DWORD vtable_rva;
    DWORD hits;
    LONG first_stack_off;
    float l,t,r,b;
    char class_name[72];
} OwnerStat;

static OwnerStat g_owner_stats[MAX_OWNER_STATS];
static DWORD g_owner_stat_count;

static int mem_readable(const void* p, DWORD bytes) {
    MEMORY_BASIC_INFORMATION mbi;
    ULONG_PTR q=(ULONG_PTR)p, base, end;
    SIZE_T n;
    if(!p || !bytes || !g_VirtualQuery) return 0;
    n=g_VirtualQuery(p,&mbi,sizeof(mbi));
    if(n<sizeof(mbi) || mbi.State!=MEM_COMMIT) return 0;
    if((mbi.Protect & PAGE_GUARD) || (mbi.Protect & PAGE_NOACCESS)) return 0;
    base=(ULONG_PTR)mbi.BaseAddress;
    end=base+mbi.RegionSize;
    if(end<base || q<base || q>end) return 0;
    return (ULONG_PTR)bytes<=end-q;
}

static int s_contains(const char* s, const char* needle) {
    unsigned int i,j,n=s_len(needle);
    if(!s || !needle || !n) return 0;
    for(i=0;s[i];++i) { for(j=0;j<n && s[i+j] && s[i+j]==needle[j];++j){} if(j==n) return 1; }
    return 0;
}

static int owner_name_interesting(const char* n) {
    if(!n || !n[0]) return 0;
    return s_contains(n,"Wnd") || s_contains(n,"Window") || s_contains(n,"UI") ||
           s_contains(n,"Dialog") || s_contains(n,"Inventory") || s_contains(n,"Status") ||
           s_contains(n,"Skill") || s_contains(n,"Equip") || s_contains(n,"Item");
}

/* MSVC x86 RTTI: vtable[-1] -> CompleteObjectLocator, COL+0x0c -> TypeDescriptor.
 * TypeDescriptor+8 is the decorated class name. */
static int rtti_name_from_object(DWORD objv, char* out, unsigned int cap, DWORD* out_vtable_rva) {
    BYTE* base=(BYTE*)g_exe; DWORD vt,col,td; const char* raw; unsigned int i=0,j=0;
    if(out_vtable_rva) *out_vtable_rva=0;
    if(!base || !g_exe_size || objv<0x10000UL || !mem_readable((void*)objv,4)) return 0;
    vt=*(DWORD*)objv;
    if(vt<(DWORD)(ULONG_PTR)base+4 || vt>=(DWORD)(ULONG_PTR)base+g_exe_size || !mem_readable((void*)(vt-4),4)) return 0;
    col=*(DWORD*)(vt-4);
    if(col<(DWORD)(ULONG_PTR)base || col+20>(DWORD)(ULONG_PTR)base+g_exe_size || !mem_readable((void*)col,20)) return 0;
    td=*(DWORD*)(col+12);
    if(td<(DWORD)(ULONG_PTR)base || td+12>(DWORD)(ULONG_PTR)base+g_exe_size || !mem_readable((void*)td,12)) return 0;
    raw=(const char*)(td+8);
    if(!(raw[0]=='.' && raw[1]=='?' && raw[2]=='A' && (raw[3]=='V' || raw[3]=='U'))) return 0;
    i=4;
    while(raw[i] && j+1<cap) {
        if(raw[i]=='@' && raw[i+1]=='@') break;
        out[j++]=raw[i++];
        if(i>140) break;
    }
    out[j]=0;
    if(!owner_name_interesting(out)) return 0;
    if(out_vtable_rva) *out_vtable_rva=vt-(DWORD)(ULONG_PTR)base;
    return j>0;
}

static void owner_reset(void) {
    DWORD i; g_owner_stat_count=0; g_owner_sample_counter=0;
    for(i=0;i<MAX_OWNER_STATS;++i) { g_owner_stats[i].object_ptr=0; g_owner_stats[i].hits=0; g_owner_stats[i].class_name[0]=0; }
}

static void owner_add(DWORD obj, DWORD vt_rva, const char* name, LONG stack_off, const UIRectF* r) {
    DWORD i; OwnerStat* st=0;
    for(i=0;i<g_owner_stat_count;++i) if(g_owner_stats[i].object_ptr==obj) { st=&g_owner_stats[i]; break; }
    if(!st) {
        if(g_owner_stat_count>=MAX_OWNER_STATS) return;
        st=&g_owner_stats[g_owner_stat_count++]; st->object_ptr=obj; st->vtable_rva=vt_rva; st->hits=0;
        st->first_stack_off=stack_off; s_copy(st->class_name,sizeof(st->class_name),name);
        st->l=r->l; st->t=r->t; st->r=r->r; st->b=r->b;
    } else {
        if(r->l<st->l)st->l=r->l; if(r->t<st->t)st->t=r->t; if(r->r>st->r)st->r=r->r; if(r->b>st->b)st->b=r->b;
    }
    ++st->hits;
}

static void owner_scan_stack(const UIRectF* r, void* frame) {
    MEMORY_BASIC_INFORMATION mbi; BYTE* q; BYTE* end; BYTE* limit; DWORD scanned=0;
    if(!g_owner_capture_active || !frame || !g_VirtualQuery) return;
    if(++g_owner_sample_counter % g_owner_sample_every) return;
    if(g_VirtualQuery(frame,&mbi,sizeof(mbi))<sizeof(mbi) || mbi.State!=MEM_COMMIT || (mbi.Protect&PAGE_GUARD) || (mbi.Protect&PAGE_NOACCESS)) return;
    q=(BYTE*)frame; end=(BYTE*)mbi.BaseAddress+mbi.RegionSize; limit=q+g_owner_scan_bytes; if(limit<q || limit>end) limit=end;
    for(;q+4<=limit;q+=4) {
        DWORD obj=*(DWORD*)q, vr=0; char name[72];
        if(rtti_name_from_object(obj,name,sizeof(name),&vr)) owner_add(obj,vr,name,(LONG)(q-(BYTE*)frame),r);
        if(++scanned>=2048) break;
    }
}

static void owner_dump_manager_lists(void) {
    /* Exact PRM 2020-09-02 singleton discovered statically: UIWindowMgr @ RVA 0xAB76D8.
       Common intrusive lists at +174/+17C/+184/+18C store object pointers at node+8. */
    static const DWORD offs[4]={0x174,0x17c,0x184,0x18c};
    BYTE* mgr; DWORD k; char line[256], name[72]; DWORD vr=0;
    if(!g_exe || g_exe_size<0xab76d8+0x200) return;
    mgr=(BYTE*)g_exe+0xab76d8;
    if(!rtti_name_from_object((DWORD)(ULONG_PTR)mgr,name,sizeof(name),&vr)) { log_line("OwnerTrace manager: RTTI validation failed"); return; }
    line[0]=0;s_append(line,sizeof(line),"OwnerTrace manager obj=");s_append_hex8(line,sizeof(line),(DWORD)(ULONG_PTR)mgr);s_append(line,sizeof(line)," class=");s_append(line,sizeof(line),name);log_line(line);
    for(k=0;k<4;++k) {
        DWORD head,node,n=0; if(!mem_readable(mgr+offs[k],4)) continue; head=*(DWORD*)(mgr+offs[k]); if(!mem_readable((void*)head,4)) continue; node=*(DWORD*)head;
        while(node && node!=head && n<128 && mem_readable((void*)node,12)) {
            DWORD obj=*(DWORD*)(node+8); name[0]=0; vr=0;
            if(rtti_name_from_object(obj,name,sizeof(name),&vr)) {
                line[0]=0;s_append(line,sizeof(line)," manager+");s_append_hex8(line,sizeof(line),offs[k]);s_append(line,sizeof(line)," obj=");s_append_hex8(line,sizeof(line),obj);s_append(line,sizeof(line)," vtRVA=");s_append_hex8(line,sizeof(line),vr);s_append(line,sizeof(line)," class=");s_append(line,sizeof(line),name);log_line(line);
            }
            node=*(DWORD*)node; ++n;
        }
    }
}

static void owner_finish_capture(void) {
    DWORD i; char line[320];
    if(!g_owner_capture_active) return;
    g_owner_capture_active=0;
    line[0]=0;s_append(line,sizeof(line),"--- OWNER TRACE END #");s_append_uint(line,sizeof(line),g_owner_capture_serial);s_append(line,sizeof(line)," candidates=");s_append_uint(line,sizeof(line),g_owner_stat_count);s_append(line,sizeof(line)," ---");log_line(line);
    for(i=0;i<g_owner_stat_count;++i) {
        OwnerStat* st=&g_owner_stats[i];
        line[0]=0;s_append(line,sizeof(line)," owner obj=");s_append_hex8(line,sizeof(line),st->object_ptr);s_append(line,sizeof(line)," vtRVA=");s_append_hex8(line,sizeof(line),st->vtable_rva);s_append(line,sizeof(line)," class=");s_append(line,sizeof(line),st->class_name);s_append(line,sizeof(line)," hits=");s_append_uint(line,sizeof(line),st->hits);s_append(line,sizeof(line)," stack+");s_append_hex8(line,sizeof(line),(DWORD)st->first_stack_off);s_append(line,sizeof(line)," bbox=");s_append_int(line,sizeof(line),(LONG)st->l);s_append(line,sizeof(line),",");s_append_int(line,sizeof(line),(LONG)st->t);s_append(line,sizeof(line),"..");s_append_int(line,sizeof(line),(LONG)st->r);s_append(line,sizeof(line),",");s_append_int(line,sizeof(line),(LONG)st->b);log_line(line);
    }
    log_line("--- END OWNER TRACE ---");
}

static void maybe_owner_trace(void) {
    short k; DWORD now;
    if(!g_owner_trace_enabled || !g_GetAsyncKeyState || !g_GetTickCount) return;
    k=g_GetAsyncKeyState(VK_OWNER_DIAGNOSTICS); now=g_GetTickCount();
    if(k&1) {
        if(g_owner_capture_active) owner_finish_capture();
        owner_reset(); ++g_owner_capture_serial; g_owner_capture_active=1; g_owner_capture_until=now+g_owner_trace_ms;
        { char line[128]; line[0]=0;s_append(line,sizeof(line),"--- OWNER TRACE START #");s_append_uint(line,sizeof(line),g_owner_capture_serial);s_append(line,sizeof(line)," (F8) ---");log_line(line); }
        owner_dump_manager_lists();
    }
    if(g_owner_capture_active && (LONG)(now-g_owner_capture_until)>=0) owner_finish_capture();
}


static void ui_group_lock(void) {
    while (__atomic_exchange_n(&g_ui_group_lock, 1, __ATOMIC_ACQUIRE)) __asm__ volatile("pause");
}
static void ui_group_unlock(void) { __atomic_store_n(&g_ui_group_lock, 0, __ATOMIC_RELEASE); }

static void owner_input_region_lock(void) {
    while (__atomic_exchange_n(&g_owner_input_region_lock, 1, __ATOMIC_ACQUIRE)) __asm__ volatile("pause");
}
static void owner_input_region_unlock(void) { __atomic_store_n(&g_owner_input_region_lock, 0, __ATOMIC_RELEASE); }

static int rect_near(const UIRectF* a, const UIRectF* b, float gap) {
    if(a->r + gap < b->l || b->r + gap < a->l) return 0;
    if(a->b + gap < b->t || b->b + gap < a->t) return 0;
    return 1;
}
static int rect_contains_point(const UIRectF* a, float x, float y) {
    return x>=a->l && x<=a->r && y>=a->t && y<=a->b;
}
static float rect_area(const UIRectF* a) {
    float w=a->r-a->l, h=a->b-a->t;
    return (w>0.0f && h>0.0f) ? w*h : 0.0f;
}
static void rect_union(UIRectF* a, const UIRectF* b) {
    if(b->l<a->l) a->l=b->l; if(b->t<a->t) a->t=b->t;
    if(b->r>a->r) a->r=b->r; if(b->b>a->b) a->b=b->b;
}
static int rect_is_global(const UIRectF* r) {
    float sw=(float)g_ui_screen_w, sh=(float)g_ui_screen_h;
    float th=((float)g_ui_global_threshold_percent)*0.01f;
    return ((r->r-r->l) >= sw*th) || ((r->b-r->t) >= sh*th);
}

static void choose_group_anchor(const UIRectF* b, float* ax, float* ay) {
    float sw=(float)g_ui_screen_w, sh=(float)g_ui_screen_h;
    if(g_ui_anchor_mode==0) { *ax=(float)g_ui_origin_x; *ay=(float)g_ui_origin_y; return; }
    if(g_ui_anchor_mode==2) { *ax=sw*0.5f; *ay=sh*0.5f; return; }
    /* Group-aware anchoring: only pick an edge when the whole group clearly
       lives in that side of the screen. A group crossing the middle is centered. */
    if(b->r <= sw*0.42f) *ax=0.0f;
    else if(b->l >= sw*0.58f) *ax=sw;
    else *ax=sw*0.5f;
    if(b->b <= sh*0.42f) *ay=0.0f;
    else if(b->t >= sh*0.58f) *ay=sh;
    else *ay=sh*0.5f;
}

static void transform_bounds(const UIRectF* src, float ax, float ay, UIRectF* dst) {
    float s=ui_scale_factor();
    dst->l=ax+(src->l-ax)*s; dst->r=ax+(src->r-ax)*s;
    dst->t=ay+(src->t-ay)*s; dst->b=ay+(src->b-ay)*s;
    if(dst->l>dst->r) { float q=dst->l; dst->l=dst->r; dst->r=q; }
    if(dst->t>dst->b) { float q=dst->t; dst->t=dst->b; dst->b=q; }
}


/* ---------- Phase 2H real UIWindow render ownership ---------- */
#define MAX_OWNER_VT_HOOKS 96
#define MAX_OWNER_WINDOWS 512
#define MAX_OWNER_MEMBERS 1024

typedef DWORD (__attribute__((thiscall)) *PFN_UIOwnerRender)(void*);

typedef struct {
    void** vt;
    void* original;
    DWORD vt_rva;
    char class_name[72];
} OwnerVtHook;

typedef struct {
    DWORD object_ptr;
    DWORD vtable_ptr;
    DWORD frame_tag;
    DWORD last_present;
    int have_anchor;
    int have_position;
    int have_input_local_bbox;
    LONG pos_x,pos_y;
    float ax,ay;
    float fit_scale,offset_x,offset_y;
    UIRectF frame_bbox;
    UIRectF input_local_bbox;
    DWORD last_input_order;
    DWORD last_input_present;
    DWORD last_draw_order;
    DWORD last_draw_present;
    DWORD bitmap_present;
    char class_name[72];
} OwnerWindowState;

typedef struct {
    UIRectF rect;
    DWORD object_ptr;
} OwnerMember;

static OwnerVtHook g_owner_vt_hooks[MAX_OWNER_VT_HOOKS];
static DWORD g_owner_vt_hook_count;
static OwnerWindowState g_owner_windows[MAX_OWNER_WINDOWS];
static DWORD g_owner_window_count;
static OwnerMember g_owner_frame_members[MAX_OWNER_MEMBERS];
static DWORD g_owner_frame_member_count;
static OwnerMember g_owner_prev_members[MAX_OWNER_MEMBERS]; /* legacy/source diagnostics */
static DWORD g_owner_prev_member_count;

/* One full learned UIWindow region per active owner. Input uses copied bounds;
 * native hit dispatch additionally validates the selected object's vtable. */
typedef struct {
    UIRectF rect;
    float ax, ay;
    float fit_scale,offset_x,offset_y;
    DWORD object_ptr;
    DWORD present;
    DWORD input_order;
    DWORD exact_order;
    DWORD vtable_ptr;
    int native_size;
} OwnerInputRegion;
static OwnerInputRegion g_owner_input_regions[MAX_OWNER_MEMBERS];
static DWORD g_owner_input_region_count;

/* Keep the owner chosen for the native mouse sample through the manager's
 * later hit query. The game can reuse a stationary sample for many frames. */
typedef struct {
    OwnerInputRegion region;
    POINT raw,mapped;
    DWORD thread;
    int valid;
} OwnerHitSelection;
typedef struct {
    DWORD target,vtable_ptr,thread;
    LONG x,y;
    int valid;
} OwnerHitScope;
static OwnerHitSelection g_owner_hit_selection;
static OwnerHitScope g_owner_hit_scope;
static int g_owner_hit_hooks_installed;
static DWORD g_owner_hit_queries,g_owner_hit_scoped,g_owner_hit_rejected,g_owner_hit_unmatched;
typedef DWORD (__attribute__((thiscall)) *PFN_UIHit)(void*,LONG,LONG);
static PFN_UIHit g_owner_hit_query;


/* Phase 2V identifies the finished UIWindow bitmap and every queued tile.
 * CPU helper paint calls are not deferred GPU commands. Keep their old matcher
 * available only when bitmap ownership is explicitly disabled or unavailable. */
static int g_owner_bitmap_enabled=1;
static int g_owner_bitmap_hooks_installed;
#define MAX_OWNER_BITMAP_DRAWS 4096
typedef struct {
    const void* verts;
    DWORD object_ptr, vtable_ptr, nverts, present;
    float ax,ay;
    float fit_scale,offset_x,offset_y;
    int native_size;
    DWORD fields[4][6];
} OwnerBitmapDrawRec;
typedef struct { DWORD object_ptr,vtable_ptr,thread; float ax,ay;
    float fit_scale,offset_x,offset_y; int native_size; } OwnerBitmapScope;
static OwnerBitmapDrawRec g_owner_bitmap_draws[MAX_OWNER_BITMAP_DRAWS];
static OwnerBitmapScope g_owner_bitmap_scope;
static volatile LONG g_owner_bitmap_lock;
static DWORD g_owner_bitmap_calls,g_owner_bitmap_submits,g_owner_bitmap_matched;
static DWORD g_owner_bitmap_overflow,g_owner_bitmap_expired,g_owner_bitmap_mismatched;
static DWORD g_owner_bitmap_unsupported,g_owner_bitmap_peak,g_owner_bitmap_offscreen;
static DWORD g_owner_bitmap_unowned;
static DWORD g_owner_bitmap_order;
static DWORD g_owner_bitmap_active_count;
static DWORD g_owner_bitmap_frame_calls;
static DWORD g_owner_map_draws;
static DWORD g_owner_minimap_draws;

#define MAX_OWNER_CAPTURE_LINKS 4096
typedef struct { DWORD object_ptr,root_owner,present; } OwnerCaptureLink;
static OwnerCaptureLink g_owner_capture_links[MAX_OWNER_CAPTURE_LINKS];
static DWORD g_owner_capture_link_count,g_owner_capture_link_overflow;
static DWORD g_owner_capture_capacity_limits,g_owner_capture_walk_limits;
static DWORD g_owner_capture_stale_roots,g_owner_capture_link_peak;
static DWORD g_owner_capture_object,g_owner_capture_root;
static float g_owner_capture_ax,g_owner_capture_ay;
static float g_owner_capture_scale,g_owner_capture_offset_x,g_owner_capture_offset_y;
static int g_owner_capture_native_size;
static DWORD g_owner_capture_maps,g_owner_capture_changes,g_owner_capture_unknown;

#define MAX_OWNER_SUBMITS 8192
typedef struct {
    UIRectF rect;
    DWORD object_ptr;
    DWORD seq;
    DWORD born_present;
    WORD hits;
    BYTE kind; /* 0=sprite helper A, 1=solid/rect helper B, 2=border helper C */
    BYTE reserved;
} OwnerSubmitRec;

static OwnerSubmitRec g_owner_submits[MAX_OWNER_SUBMITS];
static DWORD g_owner_submit_count;
static DWORD g_owner_submit_seq;
static DWORD g_owner_submit_match_cursor;
static DWORD g_owner_submit_frame_matched;
static DWORD g_owner_submit_frame_unmatched;
static DWORD g_owner_submit_frame_ambiguous;
static int g_owner_submit_hooks_installed;
static DWORD g_owner_submit_patched_a;
static DWORD g_owner_submit_patched_b;
static DWORD g_owner_submit_patched_c;

typedef DWORD (__attribute__((thiscall)) *PFN_OwnerHelperA)(void*, LONG, LONG, DWORD, DWORD);
typedef DWORD (__attribute__((thiscall)) *PFN_OwnerHelperBC)(void*, LONG, LONG, LONG, LONG, DWORD);
typedef void (__attribute__((thiscall)) *PFN_WorldRay)(void*, LONG, LONG, void*, void*, void*);
typedef void (__attribute__((thiscall)) *PFN_CursorDraw)(void*, LONG, LONG, void*, void*, DWORD, DWORD, float, float, DWORD, DWORD);
typedef void (__attribute__((thiscall)) *PFN_SpriteSubmit)(void*, void*, DWORD);
typedef DWORD (__attribute__((thiscall)) *PFN_BitmapDraw)(void*, LONG, LONG, LONG, LONG, DWORD);
typedef DWORD (__attribute__((thiscall)) *PFN_WindowOverlayDraw)(void*);
static PFN_OwnerHelperA g_owner_helper_a;
static PFN_OwnerHelperBC g_owner_helper_b;
static PFN_OwnerHelperBC g_owner_helper_c;
static PFN_WorldRay g_world_ray;
static PFN_CursorDraw g_cursor_draw;
static PFN_SpriteSubmit g_sprite_submit;
static PFN_SpriteSubmit g_owner_bitmap_submit;
static PFN_WindowOverlayDraw g_owner_overlay_draw,g_owner_special_draw,g_owner_map_draw,g_owner_minimap_draw;
void* g_owner_bitmap_primary_continue;
void* g_owner_bitmap_alternate_continue;
extern void owner_bitmap_primary_thunk(void);
extern void owner_bitmap_alternate_thunk(void);
static int vtrace_patch_rel_jmp(BYTE*, DWORD, void*);
/* Kept only because the shared thunk object still contains the old 2J entry
   stubs. They are never installed in Phase 2Q. */
void* g_owner_submit0_continue;
void* g_owner_submit1_target;
void* g_owner_submit2_continue;

static int s_equal(const char* a, const char* b) {
    unsigned int i=0; if(!a||!b) return 0;
    while(a[i] && b[i] && a[i]==b[i]) ++i;
    return a[i]==0 && b[i]==0;
}

static int owner_class_is_hover_popup(const char* n) {
    if(!n) return 0;
    /* The transient explanation factory at VA 628430 registers a real
       UITransBalloonText. Basic Info also uses UICharInfoBalloonText through
       VA 59F8D0. Neither class has the usual Wnd suffix. */
    return s_contains(n,"ToolTip") || s_contains(n,"Tooltip") ||
           s_equal(n,"UISkillDescribeWnd") || s_equal(n,"UIGuildTipWnd") ||
           s_equal(n,"UITransBalloonText") || s_equal(n,"UICharInfoBalloonText");
}

static int owner_class_is_world_label(const char* n) {
    /* C3DCooRendering projects the NPC position and moves this exact window.
       Its finished bitmap uses the normal manager draw. Scale around its live
       center, which the native placement keeps attached to the projection. */
    /* UIPlayerGage is also a manager-backed window. Scene+2C8 is placed
       from the player's current projection at VA 742788..280B. Like names,
       its class lacks Wnd; fallback grouping would retain a stale center. */
    return n && (s_equal(n,"CSignBoardWnd") || s_equal(n,"UIPlayerGage"));
}

static int owner_class_is_world_title(const char* n) {
    /* Clickable room titles are UIWindow objects, despite lacking Wnd in their
       RTTI name. Their cached bitmap includes a centered bottom pointer. */
    return n && s_equal(n,"UIChatRoomTitle");
}

static int owner_class_is_world_name(const char* n) {
    /* The hover-name factory at VA 73BFD0 registers these real UIWindows.
       Their names lack the Wnd/Window suffix used by ordinary UI admission. */
    return n && (s_equal(n,"UINameBalloonText") || s_equal(n,"UIVerticalNameBalloonText"));
}

/* Phase 2S admits the complete RTTI-named UIWindow family. Direct helper
 * callsites remain the ownership boundary; objects that are not real UI
 * windows fail this RTTI gate and pass through unchanged. */
static int owner_class_should_hook(const char* n) {
    if(!n || !n[0]) return 0;
    if(owner_class_is_hover_popup(n)) return 1;
    if(owner_class_is_world_label(n) || owner_class_is_world_title(n) || owner_class_is_world_name(n)) return 1;
    if(n[0]=='U' && n[1]=='I' && (s_contains(n,"Wnd") || s_contains(n,"Window"))) return 1;
    if(s_contains(n,"EquipWnd") || s_contains(n,"Inventory") || s_contains(n,"Skill")) return 1;
    return 0;
}

static OwnerVtHook* owner_vt_hook_for_vt(void** vt) {
    DWORD i; for(i=0;i<g_owner_vt_hook_count;++i) if(g_owner_vt_hooks[i].vt==vt) return &g_owner_vt_hooks[i];
    return 0;
}

static OwnerWindowState* owner_state_for(DWORD obj, int create) {
    DWORD i,vr=0; OwnerWindowState* st=0; void** vt=0; char name[72];
    if(!obj) return 0;
    for(i=0;i<g_owner_window_count;++i) if(g_owner_windows[i].object_ptr==obj) {
        st=&g_owner_windows[i];
        if(mem_readable((void*)obj,4) && *(DWORD*)(ULONG_PTR)obj==st->vtable_ptr) return st;
        break;
    }
    if(!create || (!st && g_owner_window_count>=MAX_OWNER_WINDOWS) || !mem_readable((void*)obj,4)) return 0;
    name[0]=0;
    if(!rtti_name_from_object(obj,name,sizeof(name),&vr) || !owner_class_should_hook(name)) return 0;
    vt=*(void***)obj; if(!vt) return 0;
    if(!st) st=&g_owner_windows[g_owner_window_count++];
    st->object_ptr=obj; st->vtable_ptr=(DWORD)(ULONG_PTR)vt; st->frame_tag=0; st->last_present=0;
    st->have_anchor=0; st->have_position=0; st->have_input_local_bbox=0; st->pos_x=0; st->pos_y=0; st->ax=0; st->ay=0;
    st->fit_scale=0; st->offset_x=st->offset_y=0;
    st->frame_bbox.l=st->frame_bbox.t=st->frame_bbox.r=st->frame_bbox.b=0;
    st->input_local_bbox.l=st->input_local_bbox.t=st->input_local_bbox.r=st->input_local_bbox.b=0;
    st->last_input_order=0; st->last_input_present=0; st->last_draw_order=0; st->last_draw_present=0; st->bitmap_present=0;
    s_copy(st->class_name,sizeof(st->class_name),name);
    return st;
}

static DWORD __attribute__((thiscall)) hook_UIOwnerRender(void* self) {
    void** vt=self?*(void***)self:0; OwnerVtHook* vh=owner_vt_hook_for_vt(vt); PFN_UIOwnerRender fn;
    DWORD old_owner=g_current_ui_owner, old_vt=g_current_ui_vtable, rv=0;
    if(!vh || !vh->original) return 0;
    fn=(PFN_UIOwnerRender)vh->original;
    g_current_ui_owner=(DWORD)(ULONG_PTR)self; g_current_ui_vtable=(DWORD)(ULONG_PTR)vt;
    rv=fn(self);
    g_current_ui_owner=old_owner; g_current_ui_vtable=old_vt;
    return rv;
}

static void owner_install_vtable(DWORD obj, DWORD vt_rva, const char* name) {
    void** vt; OwnerVtHook* vh; DWORD i, fnrva; void* orig=0; char line[256];
    if(!g_owner_scale_enabled || !obj || !owner_class_should_hook(name) || !mem_readable((void*)obj,4)) return;
    vt=*(void***)obj; if(!vt || owner_vt_hook_for_vt(vt)) return;
    if(g_owner_vt_hook_count>=MAX_OWNER_VT_HOOKS) return;
    if(!mem_readable(vt+g_owner_render_slot,4)) return;
    fnrva=ptr_to_rva(vt[g_owner_render_slot]); if(fnrva==0xffffffffUL) return;
    vh=&g_owner_vt_hooks[g_owner_vt_hook_count];
    vh->vt=vt; vh->original=0; vh->vt_rva=vt_rva; s_copy(vh->class_name,sizeof(vh->class_name),name);
    if(!patch_vtable_slot(vt,g_owner_render_slot,(void*)hook_UIOwnerRender,&orig)) { vh->vt=0; return; }
    vh->original=orig; ++g_owner_vt_hook_count;
    line[0]=0; s_append(line,sizeof(line),"Owner render hook: class="); s_append(line,sizeof(line),name);
    s_append(line,sizeof(line)," vtRVA="); s_append_hex8(line,sizeof(line),vt_rva);
    s_append(line,sizeof(line)," slot="); s_append_uint(line,sizeof(line),g_owner_render_slot);
    s_append(line,sizeof(line)," fnRVA="); s_append_hex8(line,sizeof(line),fnrva); log_line(line);
}

static void owner_install_active_vtables(void) {
    static const DWORD offs[4]={0x174,0x17c,0x184,0x18c};
    BYTE* mgr; DWORD k; char name[72]; DWORD vr=0;
    /* Phase 2Q does not patch UIWindow vtables. Direct helper calls bypassed
       the 2H slot-17 hooks, so real ownership now comes from helper ECX. */
    if(g_owner_submit_enabled) return;
    if(!g_owner_scale_enabled || !g_exe || g_exe_size<0xab76d8+0x200) return;
    mgr=(BYTE*)g_exe+0xab76d8;
    for(k=0;k<4;++k) {
        DWORD head,node,n=0; if(!mem_readable(mgr+offs[k],4)) continue; head=*(DWORD*)(mgr+offs[k]); if(!mem_readable((void*)head,4)) continue; node=*(DWORD*)head;
        while(node && node!=head && n<160 && mem_readable((void*)node,12)) {
            DWORD obj=*(DWORD*)(node+8); name[0]=0; vr=0;
            if(rtti_name_from_object(obj,name,sizeof(name),&vr)) owner_install_vtable(obj,vr,name);
            node=*(DWORD*)node; ++n;
        }
    }
}

static void owner_collect_rect(DWORD obj, const UIRectF* r) {
    OwnerWindowState* st; DWORD tag=g_ui_present_serial+1, i, start;
    if(!obj || !r || g_owner_frame_member_count>=MAX_OWNER_MEMBERS) return;
    st=owner_state_for(obj,1); if(!st) return;
    if(st->frame_tag!=tag) { st->frame_tag=tag; st->frame_bbox=*r; }
    else rect_union(&st->frame_bbox,r);
    ++g_owner_d3d_draw_order; if(!g_owner_d3d_draw_order) ++g_owner_d3d_draw_order;
    st->last_draw_order=g_owner_d3d_draw_order;
    st->last_draw_present=g_ui_present_serial+1;
    start=g_owner_frame_member_count>64?g_owner_frame_member_count-64:0;
    for(i=start;i<g_owner_frame_member_count;++i) {
        OwnerMember* m=&g_owner_frame_members[i];
        if(m->object_ptr==obj && f_abs(m->rect.l-r->l)<0.5f && f_abs(m->rect.t-r->t)<0.5f && f_abs(m->rect.r-r->r)<0.5f && f_abs(m->rect.b-r->b)<0.5f) return;
    }
    g_owner_frame_members[g_owner_frame_member_count].rect=*r;
    g_owner_frame_members[g_owner_frame_member_count].object_ptr=obj;
    ++g_owner_frame_member_count;
}


/* ---------- Phase 2Q stable real-window submission ownership ---------- */
static void owner_input_touch_state(OwnerWindowState* st) {
    if(!st) return;
    /* Hover tooltips are visual-only owners. Publishing them as input regions
       lets a noninteractive popup steal the transform from the UI underneath. */
    if(owner_class_is_hover_popup(st->class_name) || owner_class_is_world_label(st->class_name) ||
       owner_class_is_world_name(st->class_name)) return;
    ++g_owner_input_order; if(!g_owner_input_order) ++g_owner_input_order;
    st->last_input_order=g_owner_input_order;
    st->last_input_present=g_ui_present_serial+1;
}

static void owner_submit_note_bbox(DWORD obj, const UIRectF* r) {
    OwnerWindowState* st; DWORD tag=g_ui_present_serial+1;
    if(!obj || !r) return;
    st=owner_state_for(obj,1); if(!st) return;
    if(st->frame_tag!=tag) { st->frame_tag=tag; st->frame_bbox=*r; }
    else rect_union(&st->frame_bbox,r);
}

static int owner_submit_window_position(DWORD obj, OwnerWindowState* st, LONG* x, LONG* y, DWORD* invalid_reason) {
    LONG px,py; BYTE* p=(BYTE*)(ULONG_PTR)obj;
    if(invalid_reason) *invalid_reason=0;
    if(!obj || !st || !x || !y) { if(invalid_reason) *invalid_reason=1; return 0; }
    if(!mem_readable(p+g_owner_submit_pos_x_off,4) || !mem_readable(p+g_owner_submit_pos_y_off,4)) {
        if(invalid_reason) *invalid_reason=2;
        return 0;
    }
    px=*(LONG*)(p+g_owner_submit_pos_x_off); py=*(LONG*)(p+g_owner_submit_pos_y_off);
    *x=px; *y=py;
    /* Common UIWindow base code clamps these fields to the desktop/client area.
       Keep a wide guard here so partially off-screen windows are still valid. */
    if(px < -4096 || py < -4096 || px > g_ui_screen_w+4096 || py > g_ui_screen_h+4096) {
        if(invalid_reason) *invalid_reason=3;
        return 0;
    }
    st->have_position=1; st->pos_x=px; st->pos_y=py; *x=px; *y=py; return 1;
}

static void owner_submit_add_state(DWORD obj, OwnerWindowState* st, const UIRectF* in, BYTE kind) {
    UIRectF r; LONG ox=0,oy=0; DWORD pos_reason=0;
    if(!g_owner_submit_enabled || !obj || !st || !in) return;
    if(g_owner_submit_count>=MAX_OWNER_SUBMITS) { ++g_owner_submit_total_overflow; return; }
    if(owner_class_is_hover_popup(st->class_name) && !g_owner_tooltip_enabled) return;
    if(!owner_submit_window_position(obj,st,&ox,&oy,&pos_reason)) {
        char line[256];
        ++g_owner_submit_pos_invalid;
        if(pos_reason==2) ++g_owner_submit_pos_unreadable;
        else if(pos_reason==3) ++g_owner_submit_pos_range;
        g_owner_submit_pos_last_obj=obj; g_owner_submit_pos_last_x=ox; g_owner_submit_pos_last_y=oy;
        g_owner_submit_pos_last_reason=pos_reason;
        if(g_owner_submit_pos_invalid<=4) {
            line[0]=0; s_append(line,sizeof(line),"OwnerSubmit invalid position reason=");
            s_append(line,sizeof(line),pos_reason==2?"unreadable":(pos_reason==3?"range":"arguments"));
            s_append(line,sizeof(line)," obj="); s_append_hex8(line,sizeof(line),obj);
            s_append(line,sizeof(line)," class="); s_append(line,sizeof(line),st->class_name);
            if(pos_reason==3) { s_append(line,sizeof(line)," pos="); s_append_int(line,sizeof(line),ox); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),oy); }
            s_append(line,sizeof(line)," present="); s_append_uint(line,sizeof(line),g_ui_present_serial); log_line(line);
        }
        return;
    }
    r=*in;
    if(r.l>r.r) { float q=r.l; r.l=r.r; r.r=q; }
    if(r.t>r.b) { float q=r.t; r.t=r.b; r.b=q; }
    if(r.r-r.l<0.1f || r.b-r.t<0.1f) return;
    /* Learn the window-local extent from all scoped helper submissions. This
       survives deferred D3D sparsity and follows the window when it moves. */
    if(!st->have_input_local_bbox) { st->input_local_bbox=r; st->have_input_local_bbox=1; }
    else rect_union(&st->input_local_bbox,&r);
    /* Helper coordinates are local to the UIWindow. Convert to screen space
       using the base-class position fields before comparing with D3D quads. */
    r.l+=(float)ox; r.r+=(float)ox; r.t+=(float)oy; r.b+=(float)oy;
    if(r.r < -256.0f || r.b < -256.0f || r.l > (float)g_ui_screen_w+256.0f || r.t > (float)g_ui_screen_h+256.0f) return;
    g_owner_submits[g_owner_submit_count].rect=r;
    g_owner_submits[g_owner_submit_count].object_ptr=obj;
    g_owner_submits[g_owner_submit_count].seq=++g_owner_submit_seq;
    g_owner_submits[g_owner_submit_count].born_present=g_ui_present_serial;
    g_owner_submits[g_owner_submit_count].hits=0;
    g_owner_submits[g_owner_submit_count].kind=kind;
    g_owner_submits[g_owner_submit_count].reserved=0;
    ++g_owner_submit_count;
    if(g_owner_submit_count>g_owner_submit_peak_pending) g_owner_submit_peak_pending=g_owner_submit_count;
    owner_submit_note_bbox(obj,&r);
    if(kind==0) ++g_owner_submit_total_a; else if(kind==1) ++g_owner_submit_total_b; else ++g_owner_submit_total_c;
}

/* Helper A: thiscall ECX=UIWindow; args=(x,y,sprite,flags).  Static callers
 * use sprite+0x114/+0x118 as width/height, so this gives us the queued quad. */
static void owner_submit_note_a_state(DWORD obj, OwnerWindowState* st, LONG x, LONG y, DWORD sprite, DWORD flags) {
    LONG w=0,h=0; UIRectF r; (void)flags;
    if(!g_owner_submit_enabled || !sprite || !mem_readable((void*)(sprite+0x118),4)) return;
    w=*(LONG*)(sprite+0x114); h=*(LONG*)(sprite+0x118);
    if(w<=0 || h<=0 || w>4096 || h>4096) return;
    r.l=(float)x; r.t=(float)y; r.r=(float)(x+w); r.b=(float)(y+h);
    owner_submit_add_state(obj,st,&r,0);
}
void WINAPI owner_submit_note_a(DWORD obj, LONG x, LONG y, DWORD sprite, DWORD flags) {
    OwnerWindowState* st=owner_state_for(obj,1); if(!st) return;
    owner_submit_note_a_state(obj,st,x,y,sprite,flags);
}

/* Helpers B/C: thiscall ECX=UIWindow; args=(x,y,w,h,color). */
static void owner_submit_note_b_state(DWORD obj, OwnerWindowState* st, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    UIRectF r; (void)color;
    if(!g_owner_submit_enabled || w==0 || h==0 || w>8192 || w<-8192 || h>8192 || h<-8192) return;
    r.l=(float)x; r.t=(float)y; r.r=(float)(x+w); r.b=(float)(y+h);
    owner_submit_add_state(obj,st,&r,1);
}
void WINAPI owner_submit_note_b(DWORD obj, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    OwnerWindowState* st=owner_state_for(obj,1); if(!st) return;
    owner_submit_note_b_state(obj,st,x,y,w,h,color);
}
static void owner_submit_note_c_state(DWORD obj, OwnerWindowState* st, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    UIRectF r; (void)color;
    if(!g_owner_submit_enabled || w==0 || h==0 || w>8192 || w<-8192 || h>8192 || h<-8192) return;
    r.l=(float)x; r.t=(float)y; r.r=(float)(x+w); r.b=(float)(y+h);
    owner_submit_add_state(obj,st,&r,2);
}
void WINAPI owner_submit_note_c(DWORD obj, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    OwnerWindowState* st=owner_state_for(obj,1); if(!st) return;
    owner_submit_note_c_state(obj,st,x,y,w,h,color);
}

static DWORD __attribute__((thiscall)) owner_submit_scoped_a(void* self, LONG x, LONG y, DWORD sprite, DWORD flags) {
    DWORD rv=0,obj=(DWORD)(ULONG_PTR)self; OwnerWindowState* st; ++g_owner_submit_scoped_calls;
    st=owner_state_for(obj,1); owner_input_touch_state(st);
    if(st) owner_submit_note_a_state(obj,st,x,y,sprite,flags);
    if(g_owner_helper_a) rv=g_owner_helper_a(self,x,y,sprite,flags);
    return rv;
}
static DWORD __attribute__((thiscall)) owner_submit_scoped_b(void* self, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    DWORD rv=0,obj=(DWORD)(ULONG_PTR)self; OwnerWindowState* st; ++g_owner_submit_scoped_calls;
    st=owner_state_for(obj,1); owner_input_touch_state(st);
    if(st) owner_submit_note_b_state(obj,st,x,y,w,h,color);
    if(g_owner_helper_b) rv=g_owner_helper_b(self,x,y,w,h,color);
    return rv;
}
static DWORD __attribute__((thiscall)) owner_submit_scoped_c(void* self, LONG x, LONG y, LONG w, LONG h, DWORD color) {
    DWORD rv=0,obj=(DWORD)(ULONG_PTR)self; OwnerWindowState* st; ++g_owner_submit_scoped_calls;
    st=owner_state_for(obj,1); owner_input_touch_state(st);
    if(st) owner_submit_note_c_state(obj,st,x,y,w,h,color);
    if(g_owner_helper_c) rv=g_owner_helper_c(self,x,y,w,h,color);
    return rv;
}

static int owner_submit_patch_rel_call(BYTE* at, void* target) {
    DWORD oldp=0,tmp=0,rel;
    if(!at || at[0]!=0xE8 || !g_VirtualProtect) return 0;
    rel=(DWORD)((BYTE*)target-(at+5));
    if(!g_VirtualProtect(at,5,PAGE_EXECUTE_READWRITE,&oldp)) return 0;
    *(DWORD*)(at+1)=rel;
    if(g_FlushInstructionCache) g_FlushInstructionCache((HANDLE)(ULONG_PTR)-1,at,5);
    g_VirtualProtect(at,5,oldp,&tmp); return 1;
}

/* Use original APIs directly: the IAT wrapper must never see this sample.
 * Commit coordinates only after both calls succeed. A failed query must not
 * replace the caller's usable point with a partially converted screen point. */
static int input_read_raw_point(POINT* out, RECT* client) {
    POINT p; RECT r; HWND hwnd=g_input_hwnd;
    if(!out || !g_GetCursorPos || !g_real_ScreenToClient) return 0;
    if(!hwnd && g_exe && g_exe_size>=PRM_MAIN_HWND_RVA+4 &&
       mem_readable((BYTE*)g_exe+PRM_MAIN_HWND_RVA,4))
        hwnd=*(HWND*)((BYTE*)g_exe+PRM_MAIN_HWND_RVA);
    if(!hwnd || !g_GetCursorPos(&p) || !g_real_ScreenToClient(hwnd,&p)) return 0;
    if(p.x < -32768 || p.x > 32768 || p.y < -32768 || p.y > 32768) return 0;
    *out=p;
    if(client) {
        client->left=client->top=client->right=client->bottom=0;
        if(g_GetClientRect && g_GetClientRect(hwnd,&r)) *client=r;
    }
    return 1;
}

static LONG world_scale_coord(LONG value, LONG dst, LONG src) {
    LONG magnitude;
    if(value < -32768 || value > 32768 || dst<=0 || dst>16384 || src<=0 || src>16384) return value;
    /* Signed coordinates are valid outside the client; never clamp them into
       the playable area. These limits keep the product below 2^31. */
    magnitude=value<0?-value:value;
    magnitude=(magnitude*dst+src/2)/src;
    return value<0?-magnitude:magnitude;
}

static void __attribute__((thiscall)) world_ray_scoped(void* self, LONG x, LONG y,
                                                        void* camera_a, void* camera_b, void* out) {
    POINT raw; RECT client; int have_raw=0;
    LONG mapped_x=x,mapped_y=y; DWORD dx,dy; char line[320];
    ++g_world_input_calls;
    if(g_world_input_enabled) {
        have_raw=input_read_raw_point(&raw,&client);
        if(have_raw) {
            ++g_world_input_raw_uses;
            g_world_raw_x=raw.x; g_world_raw_y=raw.y;
            mapped_x=raw.x; mapped_y=raw.y;
            g_world_input_client_w=client.right-client.left;
            g_world_input_client_h=client.bottom-client.top;
        } else ++g_world_input_raw_failures;
    }
    /* +24/+28 are full dimensions; +2c/+30 are their halves used by the
       native ray's x/halfWidth-1 projection. Equal live dimensions are identity. */
    g_world_input_view_w=0; g_world_input_view_h=0;
    if(self && mem_readable((BYTE*)self+0x24,8)) {
        g_world_input_view_w=*(LONG*)((BYTE*)self+0x24);
        g_world_input_view_h=*(LONG*)((BYTE*)self+0x28);
    }
    if(have_raw && g_world_input_normalize &&
       g_world_input_view_w>=320 && g_world_input_view_w<=16384 &&
       g_world_input_view_h>=240 && g_world_input_view_h<=16384 &&
       g_world_input_client_w>=320 && g_world_input_client_w<=16384 &&
       g_world_input_client_h>=240 && g_world_input_client_h<=16384) {
        mapped_x=world_scale_coord(raw.x,g_world_input_view_w,g_world_input_client_w);
        mapped_y=world_scale_coord(raw.y,g_world_input_view_h,g_world_input_client_h);
        if(g_world_input_view_w!=g_world_input_client_w || g_world_input_view_h!=g_world_input_client_h)
            ++g_world_input_normalized;
    }
    g_world_mapped_x=mapped_x; g_world_mapped_y=mapped_y;
    dx=mapped_x>=x?(DWORD)mapped_x-(DWORD)x:(DWORD)x-(DWORD)mapped_x;
    dy=mapped_y>=y?(DWORD)mapped_y-(DWORD)y:(DWORD)y-(DWORD)mapped_y;
    if((dx>dy?dx:dy)>g_world_input_max_delta) g_world_input_max_delta=dx>dy?dx:dy;
    if(have_raw && !g_world_input_dims_logged) {
        g_world_input_dims_logged=1; line[0]=0;
        s_append(line,sizeof(line),"WorldInput first ray raw="); s_append_int(line,sizeof(line),raw.x);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),raw.y);
        s_append(line,sizeof(line)," incoming="); s_append_int(line,sizeof(line),x);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),y);
        s_append(line,sizeof(line)," mapped="); s_append_int(line,sizeof(line),mapped_x);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),mapped_y);
        s_append(line,sizeof(line)," viewport="); s_append_int(line,sizeof(line),g_world_input_view_w);
        s_append(line,sizeof(line),"x"); s_append_int(line,sizeof(line),g_world_input_view_h);
        s_append(line,sizeof(line)," client="); s_append_int(line,sizeof(line),g_world_input_client_w);
        s_append(line,sizeof(line),"x"); s_append_int(line,sizeof(line),g_world_input_client_h); log_line(line);
    }
    if(g_world_ray) g_world_ray(self,mapped_x,mapped_y,camera_a,camera_b,out);
}

static int validated_rel_call(DWORD call_rva, DWORD target_rva) {
    BYTE* at;
    if(!g_exe || call_rva>g_exe_size || g_exe_size-call_rva<5 || target_rva>=g_exe_size) return 0;
    at=(BYTE*)g_exe+call_rva;
    return at[0]==0xE8 && at+5+*(LONG*)(at+1)==(BYTE*)g_exe+target_rva;
}

static void install_world_input_hook(void) {
    if(g_world_input_hook_installed) return;
    if(!validated_rel_call(PRM_WORLD_RAY_CALL_RVA,PRM_WORLD_RAY_TARGET_RVA)) {
        log_line("WorldInput terrain-ray callsite: opcode/target mismatch"); return;
    }
    g_world_ray=(PFN_WorldRay)((BYTE*)g_exe+PRM_WORLD_RAY_TARGET_RVA);
    if(owner_submit_patch_rel_call((BYTE*)g_exe+PRM_WORLD_RAY_CALL_RVA,(void*)world_ray_scoped)) {
        g_world_input_hook_installed=1;
        log_line("WorldInput terrain-ray callsite: OK RVA=0x00334568 -> RVA=0x000A1540");
    } else log_line("WorldInput terrain-ray callsite: patch failed");
}

static void cursor_registry_lock(void) {
    while(__atomic_exchange_n(&g_cursor_draw_lock,1,__ATOMIC_ACQUIRE)) {}
}
static void cursor_registry_unlock(void) {
    __atomic_store_n(&g_cursor_draw_lock,0,__ATOMIC_RELEASE);
}
static void cursor_note_vertices(const void* verts, DWORD nverts, int is_cursor) {
    DWORD i,j,k,live=0; int slot=-1;
    if(!verts) return;
    if(is_cursor && (nverts!=4 || !mem_readable(verts,128))) {
        ++g_cursor_mismatched; is_cursor=0;
    }
    cursor_registry_lock();
    for(i=0;i<MAX_CURSOR_DRAWS;++i) {
        CursorDrawRec* r=&g_cursor_draws[i];
        if(r->verts && g_ui_present_serial-r->present>2) { r->verts=0; ++g_cursor_expired; }
        if(r->verts==verts) r->verts=0; /* invalidate pool reuse, including noncursor sprites */
        if(!r->verts) { if(slot<0) slot=(int)i; }
        else ++live;
    }
    if(is_cursor) {
        ++g_cursor_submits;
        if(slot<0) ++g_cursor_overflow;
        else {
            CursorDrawRec* r=&g_cursor_draws[slot];
            r->verts=verts; r->nverts=nverts; r->present=g_ui_present_serial;
            for(j=0;j<4;++j) {
                const DWORD* v=(const DWORD*)((const BYTE*)verts+j*32);
                for(k=0;k<4;++k) r->fields[j][k]=v[k];
                r->fields[j][4]=v[6]; r->fields[j][5]=v[7];
            }
            if(live+1>g_cursor_peak) g_cursor_peak=live+1;
        }
    }
    cursor_registry_unlock();
}

static int cursor_consume_vertices(DWORD fvf, const void* verts, DWORD nverts) {
    DWORD i,j,k; int matched=0;
    cursor_registry_lock();
    for(i=0;i<MAX_CURSOR_DRAWS;++i) {
        CursorDrawRec* r=&g_cursor_draws[i];
        if(!r->verts) continue;
        if(g_ui_present_serial-r->present>2) { r->verts=0; ++g_cursor_expired; continue; }
        if(r->verts!=verts) continue;
        r->verts=0; /* consume even on mismatch: this allocation has been reused */
        matched=(fvf==0x1C4 && nverts==r->nverts);
        for(j=0;matched && j<nverts;++j) {
            const DWORD* v=(const DWORD*)((const BYTE*)verts+j*32);
            for(k=0;k<4;++k) if(v[k]!=r->fields[j][k]) matched=0;
            if(v[6]!=r->fields[j][4] || v[7]!=r->fields[j][5]) matched=0;
        }
        if(matched) ++g_cursor_bypassed; else ++g_cursor_mismatched;
        break;
    }
    cursor_registry_unlock();
    return matched;
}

static LONG cursor_raw_coord(LONG incoming, LONG raw, LONG ui) {
    if(incoming < -65536 || incoming > 65536 || raw < -32768 || raw > 32768 ||
       ui < -32768 || ui > 32768) return incoming;
    return incoming+raw-ui; /* retain the cursor's intentional ACT/hotspot offset */
}

static void __attribute__((thiscall)) cursor_draw_scoped(void* self, LONG x, LONG y,
    void* act, void* spr, DWORD action, DWORD frame, float scale, float rotation, DWORD color, DWORD flags) {
    POINT raw; DWORD previous_thread=g_cursor_scope_thread;
    ++g_cursor_calls;
    g_cursor_scope_thread=g_GetCurrentThreadId?g_GetCurrentThreadId():0;
    if(g_exe_size>=PRM_MOUSE_Y_RVA+4 && mem_readable((BYTE*)g_exe+PRM_MOUSE_X_RVA,8) &&
       input_read_raw_point(&raw,0)) {
        x=cursor_raw_coord(x,raw.x,*(LONG*)((BYTE*)g_exe+PRM_MOUSE_X_RVA));
        y=cursor_raw_coord(y,raw.y,*(LONG*)((BYTE*)g_exe+PRM_MOUSE_Y_RVA));
        ++g_cursor_raw_uses;
    } else ++g_cursor_raw_failures;
    if(g_cursor_draw) g_cursor_draw(self,x,y,act,spr,action,frame,scale,rotation,color,flags);
    g_cursor_scope_thread=previous_thread;
}

static void __attribute__((thiscall)) cursor_sprite_submit(void* self, void* primitive, DWORD flags) {
    if(primitive && mem_readable(primitive,8)) {
        int is_cursor=g_cursor_scope_thread && g_GetCurrentThreadId &&
                      g_cursor_scope_thread==g_GetCurrentThreadId();
        cursor_note_vertices(*(void**)primitive,*(DWORD*)((BYTE*)primitive+4),is_cursor);
    }
    if(g_sprite_submit) g_sprite_submit(self,primitive,flags);
}

static void install_cursor_hooks(void) {
    if(g_cursor_hooks_installed) return;
    if(!g_GetCurrentThreadId || !validated_rel_call(PRM_CURSOR_DRAW_CALL_RVA,PRM_CURSOR_DRAW_TARGET_RVA) ||
       !validated_rel_call(PRM_SPRITE_SUBMIT_CALL_RVA,PRM_SPRITE_SUBMIT_TARGET_RVA)) {
        log_line("Cursor native hooks: opcode/target/API mismatch"); return;
    }
    g_cursor_draw=(PFN_CursorDraw)((BYTE*)g_exe+PRM_CURSOR_DRAW_TARGET_RVA);
    g_sprite_submit=(PFN_SpriteSubmit)((BYTE*)g_exe+PRM_SPRITE_SUBMIT_TARGET_RVA);
    if(owner_submit_patch_rel_call((BYTE*)g_exe+PRM_SPRITE_SUBMIT_CALL_RVA,(void*)cursor_sprite_submit) &&
       owner_submit_patch_rel_call((BYTE*)g_exe+PRM_CURSOR_DRAW_CALL_RVA,(void*)cursor_draw_scoped)) {
        g_cursor_hooks_installed=1;
        log_line("Cursor native hooks: OK draw=0x00227B7B submit=0x00227FD9");
    } else log_line("Cursor native hooks: patch failed");
}

/* Retain the correction after an edge clamp. Recomputing it from zero on each
 * frame would pin a displaced window to that edge while its native position
 * moves through the invisible overflow. Capture keeps its initial inverse;
 * subsequent native drag deltas therefore still move the visible window 1:1. */
static void owner_fit_rect(const UIRectF* whole, float ax, float ay, float* scale,
                           float* offset_x, float* offset_y) {
    float w=whole->r-whole->l,h=whole->b-whole->t;
    float sw=(float)g_ui_screen_w,sh=(float)g_ui_screen_h,l,t,r,b;
    if(w<=0.0f || h<=0.0f || sw<=0.0f || sh<=0.0f || *scale<=0.0f) return;
    if(w*(*scale)>sw) *scale=sw/w;
    if(h*(*scale)>sh) *scale=sh/h;
    l=ax+(whole->l-ax)*(*scale)+*offset_x;
    t=ay+(whole->t-ay)*(*scale)+*offset_y;
    r=l+w*(*scale); b=t+h*(*scale);
    if(l<0.0f) *offset_x-=l;
    else if(r>sw) *offset_x+=sw-r;
    if(t<0.0f) *offset_y-=t;
    else if(b>sh) *offset_y+=sh-b;
}

/* Basic Info and its icon menu are two manager roots, joined by native
 * controller layout rather than UIWindow parentage. VA 5FF205 selects menu ID
 * 0x133; ACF730 places it at basic.x, basic.y+basic.height-4. Keep that real
 * block together without merging unrelated neighboring windows. */
static DWORD owner_collect_active_objects(DWORD* out, DWORD cap);
static DWORD g_owner_fit_pair_tag,g_owner_fit_pair_basic,g_owner_fit_pair_menu;
static DWORD g_owner_fit_pair_basic_vt,g_owner_fit_pair_menu_vt;
static float g_owner_fit_pair_ax,g_owner_fit_pair_ay,g_owner_fit_pair_scale;
static float g_owner_fit_pair_dx,g_owner_fit_pair_dy;
static int owner_fit_connected(OwnerWindowState* st) {
    DWORD active[512],count,i,basic=0,menu=0; OwnerWindowState *bs=0,*ms=0;
    UIRectF joined,part; float scale;
    if(!s_equal(st->class_name,"UIBasicInfoWnd") && !s_equal(st->class_name,"UIMenuIconWnd")) return 0;
    if(g_owner_fit_pair_tag==g_ui_present_serial+1 &&
       ((st->object_ptr==g_owner_fit_pair_basic && st->vtable_ptr==g_owner_fit_pair_basic_vt) ||
        (st->object_ptr==g_owner_fit_pair_menu && st->vtable_ptr==g_owner_fit_pair_menu_vt))) {
        int have_basic=0,have_menu=0;
        BYTE* bp=(BYTE*)(ULONG_PTR)g_owner_fit_pair_basic;
        BYTE* mp=(BYTE*)(ULONG_PTR)g_owner_fit_pair_menu;
        count=owner_collect_active_objects(active,512);
        for(i=0;i<count;++i) {
            if(active[i]==g_owner_fit_pair_basic) have_basic=1;
            if(active[i]==g_owner_fit_pair_menu) have_menu=1;
        }
        if(!have_basic || !have_menu || !mem_readable(bp,0x30) || !mem_readable(mp,0x30) ||
           *(DWORD*)bp!=g_owner_fit_pair_basic_vt || *(DWORD*)mp!=g_owner_fit_pair_menu_vt ||
           *(DWORD*)(bp+0x10) || *(DWORD*)(mp+0x10) || !*(DWORD*)(bp+0x28) || !*(DWORD*)(mp+0x28) ||
           *(DWORD*)(bp+0x2c)!=0 || *(DWORD*)(mp+0x2c)!=0x133) {
            g_owner_fit_pair_tag=0; return 0;
        }
        st->ax=g_owner_fit_pair_ax; st->ay=g_owner_fit_pair_ay; st->have_anchor=1;
        st->fit_scale=g_owner_fit_pair_scale;
        st->offset_x=g_owner_fit_pair_dx; st->offset_y=g_owner_fit_pair_dy; return 1;
    }
    count=owner_collect_active_objects(active,512);
    for(i=0;i<count;++i) {
        BYTE* p=(BYTE*)(ULONG_PTR)active[i]; DWORD id; OwnerWindowState* candidate;
        if(!mem_readable(p,0x30)) continue;
        id=*(DWORD*)(p+0x2c); if(id!=0 && id!=0x133) continue;
        candidate=owner_state_for(active[i],1); if(!candidate) continue;
        if(*(DWORD*)p!=candidate->vtable_ptr || *(DWORD*)(p+0x10) || !*(DWORD*)(p+0x28)) continue;
        if(id==0 && s_equal(candidate->class_name,"UIBasicInfoWnd")) { basic=active[i]; bs=candidate; }
        if(id==0x133 && s_equal(candidate->class_name,"UIMenuIconWnd")) { menu=active[i]; ms=candidate; }
    }
    if(!basic || !menu || (st->object_ptr!=basic && st->object_ptr!=menu)) return 0;
    for(i=0;i<2;++i) {
        BYTE* p=(BYTE*)(ULONG_PTR)(i?menu:basic);
        LONG x=*(LONG*)(p+0x1c),y=*(LONG*)(p+0x20),w=*(LONG*)(p+0x14),h=*(LONG*)(p+0x18);
        if(w<=0 || h<=0 || w>8192 || h>8192 || x < -8192 || y < -8192 ||
           x>g_ui_screen_w+8192 || y>g_ui_screen_h+8192) return 0;
        part.l=(float)x; part.t=(float)y; part.r=(float)(x+w); part.b=(float)(y+h);
        if(!i) {
            joined=part;
            if(!bs->have_anchor) { choose_group_anchor(&part,&bs->ax,&bs->ay); bs->have_anchor=1; }
        } else rect_union(&joined,&part);
    }
    scale=ui_scale_factor();
    owner_fit_rect(&joined,bs->ax,bs->ay,&scale,&bs->offset_x,&bs->offset_y);
    bs->fit_scale=scale;
    ms->ax=bs->ax; ms->ay=bs->ay; ms->have_anchor=1; ms->fit_scale=scale;
    ms->offset_x=bs->offset_x; ms->offset_y=bs->offset_y;
    g_owner_fit_pair_tag=g_ui_present_serial+1;
    g_owner_fit_pair_basic=basic; g_owner_fit_pair_menu=menu;
    g_owner_fit_pair_basic_vt=bs->vtable_ptr; g_owner_fit_pair_menu_vt=ms->vtable_ptr;
    g_owner_fit_pair_ax=bs->ax; g_owner_fit_pair_ay=bs->ay; g_owner_fit_pair_scale=scale;
    g_owner_fit_pair_dx=bs->offset_x; g_owner_fit_pair_dy=bs->offset_y;
    return 1;
}

static int owner_input_select_region(const POINT*, OwnerInputRegion*, DWORD*);
static int owner_is_transient_tooltip(DWORD obj) {
    DWORD manager;
    /* The controller at E78D8C owns exactly one explanation popup at +1C.
       Other UITransBalloonText instances include actor speech (VA 719D11). */
    if(!obj || !g_exe || g_exe_size<PRM_TOOLTIP_MANAGER_RVA+4 ||
       !mem_readable((BYTE*)g_exe+PRM_TOOLTIP_MANAGER_RVA,4)) return 0;
    manager=*(DWORD*)((BYTE*)g_exe+PRM_TOOLTIP_MANAGER_RVA);
    return manager && mem_readable((BYTE*)(ULONG_PTR)manager+0x1c,4) &&
           *(DWORD*)((BYTE*)(ULONG_PTR)manager+0x1c)==obj;
}
static void owner_popup_offset(OwnerWindowState* st,LONG x,LONG y,float* dx,float* dy) {
    OwnerHitSelection hit; OwnerInputRegion current; float s;
    /* These two native factories position explanations in their source
       control's coordinates. Move only the popup origin through that owner's
       displayed transform; its cached pixels are enlarged exactly once. */
    if(!st || (!s_equal(st->class_name,"UITransBalloonText") &&
               !s_equal(st->class_name,"UICharInfoBalloonText")) ||
       !g_ui_runtime_enabled || !g_input_enabled || !g_input_runtime_enabled ||
       !g_owner_input_remap_enabled) return;
    if(s_equal(st->class_name,"UITransBalloonText") && !owner_is_transient_tooltip(st->object_ptr)) return;
    owner_input_region_lock(); hit=g_owner_hit_selection; owner_input_region_unlock();
    if(!hit.valid || !hit.region.object_ptr ||
       !owner_input_select_region(&hit.raw,&current,0) ||
       current.object_ptr!=hit.region.object_ptr || current.vtable_ptr!=hit.region.vtable_ptr ||
       current.native_size) return;
    /* The separate character-info factory caches its popup on its source
       root at +19C8. Never borrow an unrelated hovered window's transform. */
    if(s_equal(st->class_name,"UICharInfoBalloonText") &&
       (!mem_readable((BYTE*)(ULONG_PTR)current.object_ptr+0x19c8,4) ||
        *(DWORD*)((BYTE*)(ULONG_PTR)current.object_ptr+0x19c8)!=st->object_ptr)) return;
    s=current.fit_scale>0.0f?current.fit_scale:ui_scale_factor();
    *dx=current.ax+((float)x-current.ax)*s+current.offset_x-(float)x;
    *dy=current.ay+((float)y-current.ay)*s+current.offset_y-(float)y;
}

/* A UIWindow's cached pixels become one or more GPU tiles here, every frame.
 * Capture the whole-window transform once, before any tile or overlay is queued. */
static int owner_bitmap_prepare(DWORD obj, LONG x, LONG y, LONG w, LONG h) {
    OwnerWindowState* st; UIRectF whole; int native_size,world_label,world_title,world_name;
    g_owner_bitmap_scope.object_ptr=0; g_owner_bitmap_scope.thread=0;
    if(!g_owner_bitmap_hooks_installed || !g_owner_submit_enabled || !g_owner_scale_enabled) return 0;
    if(w<=0 || h<=0 || w>8192 || h>8192 || x < -8192 || y < -8192 ||
       x>g_ui_screen_w+8192 || y>g_ui_screen_h+8192) { ++g_owner_bitmap_unsupported; return 0; }
    st=owner_state_for(obj,1); if(!st) return 0;
    if(owner_class_is_hover_popup(st->class_name) && !g_owner_tooltip_enabled) return 0;
    whole.l=(float)x; whole.t=(float)y; whole.r=(float)(x+w); whole.b=(float)(y+h);
    world_label=owner_class_is_world_label(st->class_name);
    world_title=owner_class_is_world_title(st->class_name) ||
        (s_equal(st->class_name,"UITransBalloonText") && !owner_is_transient_tooltip(obj));
    world_name=owner_class_is_world_name(st->class_name);
    native_size=!world_label && !world_title && !world_name && rect_is_global(&whole) && !g_ui_scale_global;
    /* The character-info factory deliberately parks its registered popup at
       (-400,-400) while inactive (VA 59F9B6). Do not reveal that hidden cache. */
    if(s_equal(st->class_name,"UICharInfoBalloonText") && x==-400 && y==-400) native_size=1;
    if(world_label || world_title || world_name) {
        /* CSignBoardWnd placement at VA B6C430 subtracts integer half-width
           and half-height from the projected attachment. Preserve that point
           each frame instead of retaining a screen-edge anchor while it moves.
           UIChatRoomTitle is centered on the player at VA 719A89..97; its
           bitmap's bottom pointer (VA 4E6E34..5B) stays at the native position.
           Player gauges use the live centered bitmap as well (VA 742788).
           Hover names have several native layout modes (VA 73D3D0), no pointer.
           Keep their live bitmap center fixed without changing native placement. */
        st->ax=(float)(x+w/2); st->ay=(float)(y+(world_title?h:h/2)); st->have_anchor=1;
    } else if(!st->have_anchor) { choose_group_anchor(&whole,&st->ax,&st->ay); st->have_anchor=1; }
    st->fit_scale=ui_scale_factor();
    if(!g_ui_keep_on_screen || !g_ui_runtime_enabled || native_size ||
       world_label || world_title || world_name) {
        st->offset_x=st->offset_y=0.0f;
        if(!native_size) owner_popup_offset(st,x,y,&st->offset_x,&st->offset_y);
    } else {
        float ax=st->ax,ay=st->ay;
        if(owner_class_is_hover_popup(st->class_name)) {
            /* Cursor-following descriptions have no drag position to retain. */
            ax=(float)x; ay=(float)y; st->offset_x=st->offset_y=0.0f;
            owner_popup_offset(st,x,y,&st->offset_x,&st->offset_y);
        }
        if(!owner_fit_connected(st))
            owner_fit_rect(&whole,ax,ay,&st->fit_scale,&st->offset_x,&st->offset_y);
    }
    st->have_position=1; st->pos_x=x; st->pos_y=y;
    st->have_input_local_bbox=1;
    st->input_local_bbox.l=st->input_local_bbox.t=0;
    st->input_local_bbox.r=(float)w; st->input_local_bbox.b=(float)h;
    st->frame_bbox=whole; st->frame_tag=g_ui_present_serial+1;
    st->bitmap_present=g_ui_present_serial+1;
    ++g_owner_bitmap_frame_calls;
    if(world_label || world_name || (native_size && !s_equal(st->class_name,"UIRoMapWnd"))) st->last_input_order=0;
    else owner_input_touch_state(st);
    ++g_owner_bitmap_order; if(!g_owner_bitmap_order) ++g_owner_bitmap_order;
    st->last_draw_order=g_owner_bitmap_order; st->last_draw_present=g_ui_present_serial+1;
    g_owner_bitmap_scope.object_ptr=obj; g_owner_bitmap_scope.vtable_ptr=st->vtable_ptr;
    g_owner_bitmap_scope.thread=g_GetCurrentThreadId?g_GetCurrentThreadId():0;
    g_owner_bitmap_scope.ax=owner_class_is_hover_popup(st->class_name) && !world_title?(float)x:st->ax;
    g_owner_bitmap_scope.ay=owner_class_is_hover_popup(st->class_name) && !world_title?(float)y:st->ay;
    g_owner_bitmap_scope.native_size=native_size;
    g_owner_bitmap_scope.fit_scale=st->fit_scale;
    g_owner_bitmap_scope.offset_x=st->offset_x; g_owner_bitmap_scope.offset_y=st->offset_y;
    return 1;
}

DWORD WINAPI owner_bitmap_draw_c(DWORD obj, void* dc, void* original,
                                 LONG x, LONG y, LONG w, LONG h, DWORD color) {
    OwnerBitmapScope saved=g_owner_bitmap_scope; DWORD rv=0;
    ++g_owner_bitmap_calls;
    owner_bitmap_prepare(obj,x,y,w,h);
    if(original) rv=((PFN_BitmapDraw)original)(dc,x,y,w,h,color);
    g_owner_bitmap_scope=saved;
    return rv;
}

static DWORD owner_bitmap_window_draw(void* self, PFN_WindowOverlayDraw original) {
    OwnerBitmapScope saved=g_owner_bitmap_scope; DWORD rv=0;
    g_owner_bitmap_scope.object_ptr=0; g_owner_bitmap_scope.thread=0;
    if(self && mem_readable((BYTE*)self+0x14,16))
        owner_bitmap_prepare((DWORD)(ULONG_PTR)self,*(LONG*)((BYTE*)self+0x1c),
            *(LONG*)((BYTE*)self+0x20),*(LONG*)((BYTE*)self+0x14),*(LONG*)((BYTE*)self+0x18));
    if(original) rv=original(self);
    g_owner_bitmap_scope=saved;
    return rv;
}
static DWORD __attribute__((thiscall)) owner_overlay_draw_scoped(void* self) {
    return owner_bitmap_window_draw(self,g_owner_overlay_draw);
}
static DWORD __attribute__((thiscall)) owner_special_draw_scoped(void* self) {
    ++g_owner_bitmap_calls;
    return owner_bitmap_window_draw(self,g_owner_special_draw);
}
static DWORD __attribute__((thiscall)) owner_map_draw_scoped(void* self) {
    /* UIRoMapWnd renders region previews before the manager draws its cached
       bitmap. Its direct screen primitives need the same whole-map transform. */
    ++g_owner_map_draws;
    return owner_bitmap_window_draw(self,g_owner_map_draw);
}

static DWORD __attribute__((thiscall)) owner_minimap_draw_scoped(void* self) {
    OwnerBitmapScope saved=g_owner_bitmap_scope; OwnerWindowState* st; DWORD obj=0,rv=0;
    ++g_owner_minimap_draws;
    g_owner_bitmap_scope.object_ptr=0; g_owner_bitmap_scope.thread=0;
    /* Scene draw at VA 74024D emits the minimap image/markers before UIWindowMgr
       paints the controls. Its ECX is the scene, not the window. The native
       owner is UIWindowMgr+1A8 (UIMinimapZoomWnd, constructed at VA 601EB2). */
    if(g_exe && g_exe_size>=PRM_MINIMAP_WINDOW_RVA+4 &&
       mem_readable((BYTE*)g_exe+PRM_MINIMAP_WINDOW_RVA,4))
        obj=*(DWORD*)((BYTE*)g_exe+PRM_MINIMAP_WINDOW_RVA);
    if(obj && mem_readable((BYTE*)(ULONG_PTR)obj+0x14,16)) {
        st=owner_state_for(obj,1);
        if(st && s_equal(st->class_name,"UIMinimapZoomWnd"))
            owner_bitmap_prepare(obj,*(LONG*)((BYTE*)(ULONG_PTR)obj+0x1c),
                *(LONG*)((BYTE*)(ULONG_PTR)obj+0x20),*(LONG*)((BYTE*)(ULONG_PTR)obj+0x14),
                *(LONG*)((BYTE*)(ULONG_PTR)obj+0x18));
    }
    if(g_owner_minimap_draw) rv=g_owner_minimap_draw(self);
    g_owner_bitmap_scope=saved;
    return rv;
}

static void owner_bitmap_registry_lock(void) {
    while(__atomic_exchange_n(&g_owner_bitmap_lock,1,__ATOMIC_ACQUIRE)) {}
}
static void owner_bitmap_registry_unlock(void) {
    __atomic_store_n(&g_owner_bitmap_lock,0,__ATOMIC_RELEASE);
}
/* Bounded probing keeps unrelated D3D draws cheap, including a full pool of
 * reused allocations. Both insertion and lookup probe the identical 128 slots. */
#define OWNER_BITMAP_PROBES 128
static DWORD owner_bitmap_bucket(const void* verts) {
    return (DWORD)(((ULONG_PTR)verts>>4)&(MAX_OWNER_BITMAP_DRAWS-1));
}
static void owner_bitmap_forget(OwnerBitmapDrawRec* r) {
    if(r->verts) { r->verts=0; if(g_owner_bitmap_active_count) --g_owner_bitmap_active_count; }
}
static void owner_bitmap_note_vertices(const void* verts, DWORD nverts, const OwnerBitmapScope* scope) {
    DWORD i,j,k,bucket; int slot=-1,owned=scope && scope->object_ptr;
    if(!verts) return;
    if(owned && (nverts!=4 || !mem_readable(verts,128))) { ++g_owner_bitmap_unsupported; owned=0; }
    bucket=owner_bitmap_bucket(verts);
    owner_bitmap_registry_lock();
    for(i=0;i<OWNER_BITMAP_PROBES;++i) {
        DWORD at=(bucket+i)&(MAX_OWNER_BITMAP_DRAWS-1);
        OwnerBitmapDrawRec* r=&g_owner_bitmap_draws[at];
        if(r->verts && g_ui_present_serial-r->present>2) { owner_bitmap_forget(r); ++g_owner_bitmap_expired; }
        if(r->verts==verts) owner_bitmap_forget(r);
        if(!r->verts && slot<0) slot=(int)at;
    }
    if(owned) {
        ++g_owner_bitmap_submits;
        if(slot<0) ++g_owner_bitmap_overflow;
        else {
            OwnerBitmapDrawRec* r=&g_owner_bitmap_draws[slot];
            r->verts=verts; r->nverts=nverts; r->present=g_ui_present_serial;
            r->object_ptr=scope->object_ptr; r->vtable_ptr=scope->vtable_ptr;
            r->ax=scope->ax; r->ay=scope->ay; r->native_size=scope->native_size;
            r->fit_scale=scope->fit_scale;
            r->offset_x=scope->offset_x; r->offset_y=scope->offset_y;
            for(j=0;j<4;++j) {
                const DWORD* v=(const DWORD*)((const BYTE*)verts+j*32);
                for(k=0;k<4;++k) r->fields[j][k]=v[k];
                r->fields[j][4]=v[6]; r->fields[j][5]=v[7];
            }
            ++g_owner_bitmap_active_count;
            if(g_owner_bitmap_active_count>g_owner_bitmap_peak) g_owner_bitmap_peak=g_owner_bitmap_active_count;
        }
    }
    owner_bitmap_registry_unlock();
}
static int owner_bitmap_consume_transform(DWORD fvf, const void* verts, DWORD nverts,
                                          float* ax, float* ay, float* scale, float* dx, float* dy) {
    DWORD i,j,k,bucket; int matched=0;
    if(!verts) return 0;
    bucket=owner_bitmap_bucket(verts);
    owner_bitmap_registry_lock();
    for(i=0;i<OWNER_BITMAP_PROBES;++i) {
        OwnerBitmapDrawRec* r=&g_owner_bitmap_draws[(bucket+i)&(MAX_OWNER_BITMAP_DRAWS-1)];
        if(!r->verts) continue;
        if(g_ui_present_serial-r->present>2) { owner_bitmap_forget(r); ++g_owner_bitmap_expired; continue; }
        if(r->verts!=verts) continue;
        owner_bitmap_forget(r);
        matched=(fvf==0x1C4 && nverts==r->nverts);
        for(j=0;matched && j<nverts;++j) {
            const DWORD* v=(const DWORD*)((const BYTE*)verts+j*32);
            for(k=0;k<4;++k) if(v[k]!=r->fields[j][k]) matched=0;
            if(v[6]!=r->fields[j][4] || v[7]!=r->fields[j][5]) matched=0;
        }
        if(matched) {
            *ax=r->ax; *ay=r->ay;
            *scale=r->fit_scale>0.0f?r->fit_scale:ui_scale_factor();
            *dx=r->offset_x; *dy=r->offset_y;
            ++g_owner_bitmap_matched; if(r->native_size) matched=2;
        }
        else ++g_owner_bitmap_mismatched;
        break;
    }
    owner_bitmap_registry_unlock();
    return matched;
}
static int owner_bitmap_consume_vertices(DWORD fvf, const void* verts, DWORD nverts, float* ax, float* ay) {
    float scale,dx,dy;
    return owner_bitmap_consume_transform(fvf,verts,nverts,ax,ay,&scale,&dx,&dy);
}
static void __attribute__((thiscall)) owner_bitmap_queue_scoped(void* self, void* primitive, DWORD flags) {
    OwnerBitmapScope scope=g_owner_bitmap_scope;
    if(!scope.thread || !g_GetCurrentThreadId || scope.thread!=g_GetCurrentThreadId()) scope.object_ptr=0;
    if(primitive && mem_readable(primitive,8)) {
        if(!scope.object_ptr) ++g_owner_bitmap_unowned;
        owner_bitmap_note_vertices(*(void**)primitive,*(DWORD*)((BYTE*)primitive+4),&scope);
    }
    if(g_owner_bitmap_submit) g_owner_bitmap_submit(self,primitive,flags);
}

static int owner_bitmap_patch_span_valid(DWORD rva, BYTE slot) {
    BYTE* p=(BYTE*)g_exe+rva;
    return g_exe && g_exe_size>=rva+6 && p[0]==0xff && p[1]==0x53 && p[2]==slot &&
           p[3]==0x8b && p[4]==0x5d && p[5]==0xdc;
}
static void install_owner_bitmap_hooks(void) {
    BYTE* base=(BYTE*)g_exe;
    if(!g_owner_bitmap_enabled || !g_owner_submit_enabled || g_owner_bitmap_hooks_installed) return;
    if(!g_GetCurrentThreadId || !owner_bitmap_patch_span_valid(PRM_BITMAP_PRIMARY_RVA,0x28) ||
       !owner_bitmap_patch_span_valid(PRM_BITMAP_ALTERNATE_RVA,0x0c) ||
       !validated_rel_call(PRM_BITMAP_QUEUE_CALL_RVA,PRM_BITMAP_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_OVERLAY_DRAW_CALL_RVA,PRM_OVERLAY_DRAW_TARGET_RVA) ||
       !validated_rel_call(PRM_OVERLAY_QUEUE_CALL_RVA,PRM_OVERLAY_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_MAP_DRAW_CALL_RVA,PRM_MAP_DRAW_TARGET_RVA) ||
       !validated_rel_call(PRM_MINIMAP_DRAW_CALL_RVA,PRM_MINIMAP_DRAW_TARGET_RVA) ||
       !validated_rel_call(PRM_MINIMAP_QUEUE_CALL_RVA,PRM_MINIMAP_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_MINIMAP_MARKER_QUEUE_CALL_RVA,PRM_MINIMAP_MARKER_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_RECT_QUEUE_CALL_RVA,PRM_RECT_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_IMAGE_QUEUE_CALL_RVA,PRM_IMAGE_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_PREVIEW_QUEUE_CALL_RVA,PRM_PREVIEW_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_MAP_LINE_QUEUE_CALL_RVA,PRM_MAP_LINE_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_MAP_ARROW_QUEUE_CALL_RVA,PRM_MAP_ARROW_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_MAP_SPRITE_QUEUE_CALL_RVA,PRM_MAP_SPRITE_QUEUE_TARGET_RVA) ||
       !validated_rel_call(PRM_SPECIAL_DRAW_CALL_RVA,PRM_SPECIAL_DRAW_TARGET_RVA)) {
        log_line("OwnerBitmap hooks: opcode/target/API mismatch"); return;
    }
    g_owner_bitmap_submit=(PFN_SpriteSubmit)(base+PRM_BITMAP_QUEUE_TARGET_RVA);
    g_owner_overlay_draw=(PFN_WindowOverlayDraw)(base+PRM_OVERLAY_DRAW_TARGET_RVA);
    g_owner_special_draw=(PFN_WindowOverlayDraw)(base+PRM_SPECIAL_DRAW_TARGET_RVA);
    g_owner_map_draw=(PFN_WindowOverlayDraw)(base+PRM_MAP_DRAW_TARGET_RVA);
    g_owner_minimap_draw=(PFN_WindowOverlayDraw)(base+PRM_MINIMAP_DRAW_TARGET_RVA);
    g_owner_bitmap_primary_continue=base+PRM_BITMAP_PRIMARY_RVA+6;
    g_owner_bitmap_alternate_continue=base+PRM_BITMAP_ALTERNATE_RVA+6;
    /* Install queue consumers first. If a later patch fails, scope remains off
       and all wrappers forward their original calls without assigning owners. */
    if(owner_submit_patch_rel_call(base+PRM_BITMAP_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_OVERLAY_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_RECT_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_IMAGE_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_PREVIEW_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MAP_LINE_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MAP_ARROW_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MAP_SPRITE_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MINIMAP_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MINIMAP_MARKER_QUEUE_CALL_RVA,(void*)owner_bitmap_queue_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MINIMAP_DRAW_CALL_RVA,(void*)owner_minimap_draw_scoped) &&
       owner_submit_patch_rel_call(base+PRM_MAP_DRAW_CALL_RVA,(void*)owner_map_draw_scoped) &&
       owner_submit_patch_rel_call(base+PRM_OVERLAY_DRAW_CALL_RVA,(void*)owner_overlay_draw_scoped) &&
       owner_submit_patch_rel_call(base+PRM_SPECIAL_DRAW_CALL_RVA,(void*)owner_special_draw_scoped) &&
       vtrace_patch_rel_jmp(base+PRM_BITMAP_PRIMARY_RVA,6,(void*)owner_bitmap_primary_thunk) &&
       vtrace_patch_rel_jmp(base+PRM_BITMAP_ALTERNATE_RVA,6,(void*)owner_bitmap_alternate_thunk)) {
        g_owner_bitmap_hooks_installed=1;
        log_line("OwnerBitmap hooks: OK bitmap=2 overlay=1 special=1 map=1 minimap=1 queue=10 offscreen=2");
    } else log_line("OwnerBitmap hooks: patch failed; owner scopes disabled");
}

static int owner_submit_text_range(BYTE** start, DWORD* size) {
    BYTE* base=(BYTE*)g_exe; BYTE* coff; BYTE* opt; BYTE* sec;
    DWORD peoff,nsects,optsz,i;
    if(start) *start=0; if(size) *size=0;
    if(!base || !start || !size || *(WORD*)base!=0x5a4d) return 0;
    peoff=*(DWORD*)(base+0x3c);
    if(*(DWORD*)(base+peoff)!=0x00004550UL) return 0;
    coff=base+peoff+4; nsects=*(WORD*)(coff+2); optsz=*(WORD*)(coff+16);
    opt=coff+20; sec=opt+optsz;
    for(i=0;i<nsects;++i,sec+=40) {
        if(sec[0]=='.' && sec[1]=='t' && sec[2]=='e' && sec[3]=='x' && sec[4]=='t') {
            DWORD rva=*(DWORD*)(sec+12),vsize=*(DWORD*)(sec+8);
            if(!rva || !vsize || rva>=g_exe_size || vsize>g_exe_size-rva) return 0;
            *start=base+rva; *size=vsize; return 1;
        }
    }
    return 0;
}

/* Phase 2S patches every direct executable call to the three validated
 * UIWindow drawing helpers. The helper entries themselves remain untouched.
 * Each wrapper gates ownership through the runtime RTTI of ECX, so non-window
 * callers retain their original behavior without publishing owner state. */
static void owner_submit_patch_all_window_calls(void) {
    BYTE* p; BYTE* end; DWORD text_size=0;
    if(!owner_submit_text_range(&p,&text_size)) { log_line("OwnerSubmit all-window scan: .text not found"); return; }
    end=p+text_size;
    while(p+5<=end) {
        if(p[0]==0xE8) {
            LONG rel=*(LONG*)(p+1); BYTE* dst=p+5+rel; void* hook=0; int kind=-1;
            if(dst==(BYTE*)g_owner_helper_a) { hook=(void*)owner_submit_scoped_a; kind=0; }
            else if(dst==(BYTE*)g_owner_helper_b) { hook=(void*)owner_submit_scoped_b; kind=1; }
            else if(dst==(BYTE*)g_owner_helper_c) { hook=(void*)owner_submit_scoped_c; kind=2; }
            if(hook && owner_submit_patch_rel_call(p,hook)) {
                if(kind==0) ++g_owner_submit_patched_a;
                else if(kind==1) ++g_owner_submit_patched_b;
                else ++g_owner_submit_patched_c;
                p+=5; continue;
            }
        }
        ++p;
    }
}

static void owner_submit_patch_render_range(const char* name, DWORD first_rva, DWORD end_rva) {
    BYTE* base=(BYTE*)g_exe; BYTE* p; BYTE* end; DWORD a=0,b=0,c=0; char line[256];
    if(!base || first_rva>=end_rva || end_rva>=g_exe_size) return;
    p=base+first_rva; end=base+end_rva;
    while(p+5<=end) {
        if(p[0]==0xE8) {
            LONG rel=*(LONG*)(p+1); BYTE* dst=p+5+rel; void* hook=0; int kind=-1;
            if(dst==base+0x0071C0B0UL) { hook=(void*)owner_submit_scoped_a; kind=0; }
            else if(dst==base+0x0071C230UL) { hook=(void*)owner_submit_scoped_b; kind=1; }
            else if(dst==base+0x0071C4D0UL) { hook=(void*)owner_submit_scoped_c; kind=2; }
            if(hook && owner_submit_patch_rel_call(p,hook)) {
                if(kind==0) { ++a; ++g_owner_submit_patched_a; }
                else if(kind==1) { ++b; ++g_owner_submit_patched_b; }
                else { ++c; ++g_owner_submit_patched_c; }
            }
        }
        ++p;
    }
    line[0]=0; s_append(line,sizeof(line),"OwnerSubmit scoped calls: class="); s_append(line,sizeof(line),name);
    s_append(line,sizeof(line)," A="); s_append_uint(line,sizeof(line),a);
    s_append(line,sizeof(line)," B="); s_append_uint(line,sizeof(line),b);
    s_append(line,sizeof(line)," C="); s_append_uint(line,sizeof(line),c); log_line(line);
}

static void owner_submit_install_hooks(void) {
    BYTE* base=(BYTE*)g_exe; char line[224];
    if(g_owner_submit_hooks_installed || !g_owner_submit_enabled || !base) return;
    if(g_owner_bitmap_hooks_installed) {
        log_line("OwnerSubmit legacy helper matcher: inactive (whole-window bitmap ownership)"); return;
    }
    g_owner_helper_a=(PFN_OwnerHelperA)(base+0x0071C0B0UL);
    g_owner_helper_b=(PFN_OwnerHelperBC)(base+0x0071C230UL);
    g_owner_helper_c=(PFN_OwnerHelperBC)(base+0x0071C4D0UL);

    if(g_owner_all_window_calls) {
        owner_submit_patch_all_window_calls();
    } else {
        /* Reversible Phase 2Q comparison mode: only the three proven movable
         * windows are intercepted. */
        owner_submit_patch_render_range("UIStatusWnd",0x00151690UL,0x00152444UL);
        owner_submit_patch_render_range("UIItemWnd",0x001CD190UL,0x001CD958UL);
        owner_submit_patch_render_range("UINewSkillListWnd",0x00787CF0UL,0x0078810FUL);
    }

    line[0]=0; s_append(line,sizeof(line),"OwnerSubmit scoped hooks total A="); s_append_uint(line,sizeof(line),g_owner_submit_patched_a);
    s_append(line,sizeof(line)," B="); s_append_uint(line,sizeof(line),g_owner_submit_patched_b);
    s_append(line,sizeof(line)," C="); s_append_uint(line,sizeof(line),g_owner_submit_patched_c); log_line(line);
    if(g_owner_all_window_calls &&
       (g_owner_submit_patched_a!=543UL || g_owner_submit_patched_b!=405UL || g_owner_submit_patched_c!=38UL))
        log_line("OwnerSubmit WARNING: all-window call count differs from this PRM build");
    if(!g_owner_all_window_calls &&
       g_owner_submit_patched_a+g_owner_submit_patched_b+g_owner_submit_patched_c!=20UL)
        log_line("OwnerSubmit WARNING: scoped helper call count differs from this PRM build");
    g_owner_submit_hooks_installed=1;
}

static DWORD owner_submit_max_hits(BYTE kind) { return kind==2 ? 24UL : (kind==1 ? 4UL : 2UL); }

static int owner_submit_match_rect(const UIRectF* r, DWORD* obj_out) {
    DWORD i,best=0xffffffffUL,second=0xffffffffUL,best_exact=0xffffffffUL,best_exact_seq=0;
    DWORD exact_first_owner=0,exact_count=0; int exact_multi_owner=0;
    float best_score=1.0e30f,second_score=1.0e30f;
    float tol=(float)g_owner_submit_tolerance, area_r;
    if(obj_out) *obj_out=0;
    if(!g_owner_submit_enabled || !r || !g_owner_submit_count) return 0;
    area_r=rect_area(r);
    for(i=0;i<g_owner_submit_count;++i) {
        OwnerSubmitRec* q=&g_owner_submits[i]; float edge,area_q,score,order; int exact,inside;
        if(!q->object_ptr || q->hits>=owner_submit_max_hits(q->kind)) continue;
        edge=f_abs(r->l-q->rect.l)+f_abs(r->t-q->rect.t)+f_abs(r->r-q->rect.r)+f_abs(r->b-q->rect.b);
        exact = edge <= tol*4.0f;
        inside = r->l>=q->rect.l-tol && r->t>=q->rect.t-tol && r->r<=q->rect.r+tol && r->b<=q->rect.b+tol;
        area_q=rect_area(&q->rect);
        if(q->kind==0) {
            /* Sprite: usually one exact quad; allow clipping against a window edge. */
            if(!exact && !(inside && area_r>=area_q*0.20f)) continue;
        } else if(q->kind==1) {
            /* Filled rectangle can be clipped but should occupy a meaningful fraction. */
            if(!exact && !(inside && area_r>=area_q*0.15f)) continue;
        } else {
            /* Border helper emits several thin rectangles inside one submitted box. */
            if(!inside && !exact) continue;
        }

        /* With a longer retained queue, old and new submissions can describe the
           same exact rectangle. Exact geometry is strongest evidence, so when
           several exact records exist prefer the newest sequence number. */
        if(exact) {
            ++exact_count;
            if(!exact_first_owner) exact_first_owner=q->object_ptr;
            else if(exact_first_owner!=q->object_ptr) exact_multi_owner=1;
            if(best_exact==0xffffffffUL || q->seq>best_exact_seq) {
                best_exact=i; best_exact_seq=q->seq;
            }
            continue;
        }

        order = i>=g_owner_submit_match_cursor ? (float)(i-g_owner_submit_match_cursor) : (float)(g_owner_submit_count+i-g_owner_submit_match_cursor);
        score=100.0f+edge*0.25f+order*0.02f;
        if(q->kind==2) score += area_q>area_r ? (area_q-area_r)*0.00002f : 0.0f;
        if(score<best_score) { second=best; second_score=best_score; best=i; best_score=score; }
        else if(score<second_score) { second=i; second_score=score; }
    }

    if(best_exact!=0xffffffffUL) {
        if(exact_count>1) ++g_owner_submit_newest_exact_choices;
        best=best_exact; second=0xffffffffUL; best_score=0.0f; second_score=1.0e30f;
        if(exact_multi_owner) { ++g_owner_submit_frame_ambiguous; ++g_owner_submit_total_ambiguous; }
    } else {
        if(best==0xffffffffUL) { if(g_owner_submit_count) ++g_owner_submit_frame_unmatched; return 0; }
        if(second!=0xffffffffUL && second_score-best_score<1.0f && g_owner_submits[second].object_ptr!=g_owner_submits[best].object_ptr) {
            ++g_owner_submit_frame_ambiguous; ++g_owner_submit_total_ambiguous;
        }
    }

    ++g_owner_submits[best].hits;
    {
        DWORD age = g_ui_present_serial>=g_owner_submits[best].born_present ?
                    g_ui_present_serial-g_owner_submits[best].born_present : 0;
        DWORD bin = age < (OWNER_AGE_HIST_BINS-1) ? age : (OWNER_AGE_HIST_BINS-1);
        if(age>g_owner_submit_match_age_max) g_owner_submit_match_age_max=age;
        ++g_owner_submit_age_hist[bin];
    }
    if(g_owner_submits[best].hits>=owner_submit_max_hits(g_owner_submits[best].kind)) g_owner_submit_match_cursor=(best+1)%g_owner_submit_count;
    else g_owner_submit_match_cursor=best;
    if(obj_out) *obj_out=g_owner_submits[best].object_ptr;
    ++g_owner_submit_frame_matched; ++g_owner_submit_total_matched;
    return 1;
}

/* Legacy comparison mode retains CPU paint rectangles for its heuristic matcher.
 * Phase 2V static analysis established that A/B/C paint cached pixels; measured
 * rectangle-match age is not GPU queue latency. The original 96-present setting
 * stays intact for comparison; exact bitmap ownership does not use this queue. */
static void owner_submit_finish_present(void) {
    DWORD i,n=0,expired=0;
    g_owner_submit_last_matched=g_owner_submit_frame_matched;
    g_owner_submit_last_unmatched=g_owner_submit_frame_unmatched;
    g_owner_submit_last_ambiguous=g_owner_submit_frame_ambiguous;
    for(i=0;i<g_owner_submit_count;++i) {
        OwnerSubmitRec q=g_owner_submits[i];
        DWORD age = g_ui_present_serial>=q.born_present ? g_ui_present_serial-q.born_present : 0;
        if(q.hits>=owner_submit_max_hits(q.kind) || age>g_owner_submit_max_age_presents) {
            if(age>g_owner_submit_max_age_presents) { ++expired; ++g_owner_submit_total_expired; }
            continue;
        }
        if(n!=i) g_owner_submits[n]=q;
        ++n;
    }
    g_owner_submit_count=n;
    g_owner_submit_last_count=n;
    g_owner_submit_last_expired=expired;
    g_owner_submit_match_cursor=0;
    g_owner_submit_frame_matched=0; g_owner_submit_frame_unmatched=0; g_owner_submit_frame_ambiguous=0;
}

static int owner_get_transform(DWORD obj, float* ax, float* ay) {
    OwnerWindowState* st=owner_state_for(obj,0); if(!st) return 0;
    /* Preserve the tooltip origin while enlarging it. A screen-edge anchor
       would move a cursor-following popup and can make it jump between sides. */
    if(owner_class_is_hover_popup(st->class_name) && st->have_position) {
        *ax=(float)st->pos_x; *ay=(float)st->pos_y; return 1;
    }
    if(!st->have_anchor) return 0;
    *ax=st->ax; *ay=st->ay; return 1;
}

#define MAX_OWNER_ACTIVE_OBJECTS 512
static DWORD owner_collect_active_objects(DWORD* out, DWORD cap) {
    static const DWORD offs[4]={0x174,0x17c,0x184,0x18c};
    BYTE* mgr; DWORD k,nout=0;
    if(!out || !cap || !g_exe || g_exe_size<0xab76d8+0x200) return 0;
    mgr=(BYTE*)g_exe+0xab76d8;
    for(k=0;k<4 && nout<cap;++k) {
        DWORD head,node,guard=0;
        if(!mem_readable(mgr+offs[k],4)) continue;
        head=*(DWORD*)(mgr+offs[k]); if(!head || !mem_readable((void*)head,4)) continue;
        node=*(DWORD*)head;
        while(node && node!=head && guard<256 && nout<cap && mem_readable((void*)node,12)) {
            DWORD obj=*(DWORD*)(node+8),j; int dup=0;
            if(obj) {
                for(j=0;j<nout;++j) if(out[j]==obj) { dup=1; break; }
                if(!dup) out[nout++]=obj;
            }
            node=*(DWORD*)node; ++guard;
        }
    }
    return nout;
}

static int owner_active_contains(const DWORD* objs, DWORD count, DWORD obj) {
    DWORD i; if(!objs || !obj) return 0;
    for(i=0;i<count;++i) if(objs[i]==obj) return 1;
    return 0;
}

/* Build descendant-to-root aliases on the render thread. Input only consumes
 * copied pointers and transforms; it never walks live UIWindow objects. */
static OwnerCaptureLink g_owner_capture_build[MAX_OWNER_CAPTURE_LINKS];
static DWORD g_owner_capture_build_count;
static void owner_capture_note_limit(DWORD reason, DWORD root, DWORD obj, DWORD node) {
    char line[256];
    ++g_owner_capture_link_overflow;
    if(reason==3) ++g_owner_capture_walk_limits; else ++g_owner_capture_capacity_limits;
    /* Preserve the first offending objects without adding per-frame log I/O.
       F8 retains cumulative counts after this small event budget is exhausted. */
    if(g_owner_capture_link_overflow>4) return;
    line[0]=0; s_append(line,sizeof(line),"OwnerCapture limit reason=");
    s_append(line,sizeof(line),reason==1?"aliases":reason==2?"pending":"siblings");
    s_append(line,sizeof(line)," present="); s_append_uint(line,sizeof(line),g_ui_present_serial);
    s_append(line,sizeof(line)," root="); s_append_hex8(line,sizeof(line),root);
    s_append(line,sizeof(line)," object="); s_append_hex8(line,sizeof(line),obj);
    s_append(line,sizeof(line)," node="); s_append_hex8(line,sizeof(line),node);
    s_append(line,sizeof(line)," links="); s_append_uint(line,sizeof(line),g_owner_capture_build_count);
    log_line(line);
}
static void owner_capture_build_tree(DWORD root) {
    static DWORD pending[MAX_OWNER_CAPTURE_LINKS];
    DWORD count=1;
    pending[0]=root;
    while(count) {
        DWORD obj=pending[--count],i,head,node,guard=0; int seen=0;
        for(i=0;i<g_owner_capture_build_count;++i) if(g_owner_capture_build[i].object_ptr==obj) { seen=1; break; }
        if(seen || !mem_readable((void*)(ULONG_PTR)obj,0x54)) continue;
        if(g_owner_capture_build_count>=MAX_OWNER_CAPTURE_LINKS) {
            owner_capture_note_limit(1,root,obj,0); return;
        }
        g_owner_capture_build[g_owner_capture_build_count].object_ptr=obj;
        g_owner_capture_build[g_owner_capture_build_count].root_owner=root;
        g_owner_capture_build[g_owner_capture_build_count++].present=g_ui_present_serial;
        head=*(DWORD*)(ULONG_PTR)(obj+0x50);
        if(!head || !mem_readable((void*)(ULONG_PTR)head,4)) continue;
        node=*(DWORD*)(ULONG_PTR)head;
        while(node && node!=head && mem_readable((void*)(ULONG_PTR)node,12)) {
            DWORD child;
            /* Reaching the sentinel after exactly 512 children is complete.
               Only an additional readable node means traversal was truncated. */
            if(guard>=512) { owner_capture_note_limit(3,root,obj,node); break; }
            ++guard;
            child=*(DWORD*)(ULONG_PTR)(node+8);
            if(child && child!=obj && mem_readable((void*)(ULONG_PTR)(child+0x10),4) &&
               *(DWORD*)(ULONG_PTR)(child+0x10)==obj) {
                if(count<MAX_OWNER_CAPTURE_LINKS) pending[count++]=child;
                else owner_capture_note_limit(2,root,obj,node);
            }
            node=*(DWORD*)(ULONG_PTR)node;
        }
    }
}
static void owner_capture_build_snapshot(void) {
    DWORD i;
    g_owner_capture_build_count=0;
    if(!g_owner_bitmap_hooks_installed) return;
    for(i=0;i<g_owner_window_count;++i) {
        OwnerWindowState* st=&g_owner_windows[i];
        if(!st->bitmap_present || g_ui_present_serial-st->bitmap_present>2 ||
           owner_class_is_hover_popup(st->class_name) ||
           owner_class_is_world_label(st->class_name) || owner_class_is_world_name(st->class_name)) continue;
        /* Recent drawing is not a lifetime guarantee. Match the same object
           identity required by input publication before reading its child list. */
        if(!mem_readable((void*)(ULONG_PTR)st->object_ptr,4) ||
           *(DWORD*)(ULONG_PTR)st->object_ptr!=st->vtable_ptr) {
            ++g_owner_capture_stale_roots; continue;
        }
        owner_capture_build_tree(st->object_ptr);
    }
    if(g_owner_capture_build_count>g_owner_capture_link_peak)
        g_owner_capture_link_peak=g_owner_capture_build_count;
}
static DWORD owner_native_capture(void) {
    if(!g_owner_bitmap_hooks_installed || !g_exe || g_exe_size<PRM_UI_CAPTURE_RVA+4 ||
       !mem_readable((BYTE*)g_exe+PRM_UI_CAPTURE_RVA,4)) return 0;
    return *(DWORD*)((BYTE*)g_exe+PRM_UI_CAPTURE_RVA);
}
static int owner_input_apply_transform(POINT* p, float ax, float ay) {
    float sc=ui_scale_factor(),x,y;
    if(!p || sc<0.01f) return 0;
    x=ax+((float)p->x-ax)/sc; y=ay+((float)p->y-ay)/sc;
    p->x=(LONG)(x>=0.0f?x+0.5f:x-0.5f);
    p->y=(LONG)(y>=0.0f?y+0.5f:y-0.5f);
    return 1;
}
static void owner_input_region_bounds(const OwnerInputRegion* r, UIRectF* dst) {
    float sc=r->fit_scale>0.0f?r->fit_scale:ui_scale_factor();
    if(r->native_size) { *dst=r->rect; return; }
    dst->l=r->ax+(r->rect.l-r->ax)*sc+r->offset_x;
    dst->r=r->ax+(r->rect.r-r->ax)*sc+r->offset_x;
    dst->t=r->ay+(r->rect.t-r->ay)*sc+r->offset_y;
    dst->b=r->ay+(r->rect.b-r->ay)*sc+r->offset_y;
}
static int owner_input_map_region(POINT* p, const OwnerInputRegion* r) {
    float sc,x,y;
    if(!p) return 0;
    if(r->native_size) return 1;
    sc=r->fit_scale>0.0f?r->fit_scale:ui_scale_factor();
    if(sc<0.01f) return 0;
    x=r->ax+((float)p->x-r->ax-r->offset_x)/sc;
    y=r->ay+((float)p->y-r->ay-r->offset_y)/sc;
    p->x=(LONG)(x>=0.0f?x+0.5f:x-0.5f);
    p->y=(LONG)(y>=0.0f?y+0.5f:y-0.5f);
    return 1;
}
static int owner_input_map_capture(POINT* p, DWORD captured) {
    DWORD i,root=0; OwnerInputRegion region={0}; float ax=0,ay=0; int found=0,native_size=0;
    owner_input_region_lock();
    if(captured!=g_owner_capture_object) {
        g_owner_capture_object=captured; g_owner_capture_root=0; g_owner_capture_native_size=0;
        if(captured) ++g_owner_capture_changes;
    }
    if(captured && g_owner_capture_root) {
        root=g_owner_capture_root; ax=g_owner_capture_ax; ay=g_owner_capture_ay; found=1;
        native_size=g_owner_capture_native_size;
        region.fit_scale=g_owner_capture_scale;
        region.offset_x=g_owner_capture_offset_x; region.offset_y=g_owner_capture_offset_y;
    } else if(captured) {
        /* Prefer a captured root itself over a descendant alias. */
        for(i=0;i<g_owner_input_region_count;++i)
            if(g_owner_input_regions[i].object_ptr==captured) { root=captured; break; }
        if(!root) for(i=0;i<g_owner_capture_link_count;++i) {
            OwnerCaptureLink* link=&g_owner_capture_links[i];
            if(link->object_ptr==captured && g_ui_present_serial-link->present<=2) { root=link->root_owner; break; }
        }
        if(root) for(i=0;i<g_owner_input_region_count;++i) {
            OwnerInputRegion* r=&g_owner_input_regions[i];
            if(r->object_ptr==root && g_ui_present_serial-r->present<=2) {
                ax=r->ax; ay=r->ay; found=1; native_size=r->native_size;
                g_owner_capture_root=root; g_owner_capture_ax=ax; g_owner_capture_ay=ay;
                g_owner_capture_native_size=native_size;
                region=*r;
                g_owner_capture_scale=r->fit_scale;
                g_owner_capture_offset_x=r->offset_x; g_owner_capture_offset_y=r->offset_y;
                break;
            }
        }
    }
    owner_input_region_unlock();
    if(!found) { if(captured) ++g_owner_capture_unknown; return 0; }
    region.ax=ax; region.ay=ay; region.native_size=native_size;
    if(!owner_input_map_region(p,&region)) return 0;
    ++g_owner_capture_maps; ++g_owner_mapped_mouse;
    return 1;
}

static void owner_finalize_frame(void) {
    DWORD i,n=0,rn=0,active_n=0,manager_regions=0,grace_regions=0;
    DWORD active_objs[MAX_OWNER_ACTIVE_OBJECTS];
    active_n=owner_collect_active_objects(active_objs,MAX_OWNER_ACTIVE_OBJECTS);
    for(i=0;i<g_owner_window_count;++i) {
        OwnerWindowState* st=&g_owner_windows[i];
        if(st->frame_tag==g_ui_present_serial) {
            if(!st->have_anchor) { choose_group_anchor(&st->frame_bbox,&st->ax,&st->ay); st->have_anchor=1; }
            st->last_present=g_ui_present_serial;
        }
    }

    /* Phase 2Q: input activity is independent of deferred D3D matching. A
       learned owner qualifies while it is in UIWindowMgr's active lists. A
       short helper-activity grace period covers transient manager-list timing.
       Exact D3D order is copied only when it is fresh enough to be a useful
       z-order hint; otherwise the scoped helper input order decides overlaps. */
    owner_capture_build_snapshot();
    owner_input_region_lock();
    for(i=0;i<g_owner_capture_build_count;++i) g_owner_capture_links[i]=g_owner_capture_build[i];
    g_owner_capture_link_count=g_owner_capture_build_count;
    for(i=0;i<g_owner_window_count && rn<MAX_OWNER_MEMBERS;++i) {
        OwnerWindowState* st=&g_owner_windows[i]; UIRectF local,src; LONG ox=0,oy=0;
        DWORD input_age,draw_age,exact_order=0; int manager_active,grace_active,native_size;
        if(!st->have_anchor || !st->have_input_local_bbox || !st->last_input_order) continue;
        if(!mem_readable((void*)(ULONG_PTR)st->object_ptr,4) ||
           *(DWORD*)(ULONG_PTR)st->object_ptr!=st->vtable_ptr) continue;
        manager_active=owner_active_contains(active_objs,active_n,st->object_ptr);
        input_age=g_ui_present_serial>=st->last_input_present ? g_ui_present_serial-st->last_input_present : 0;
        grace_active=st->last_input_present && input_age<=g_owner_input_max_age_presents;
        if(!manager_active && !grace_active) continue;
        if(g_owner_bitmap_hooks_installed) {
            if(!st->bitmap_present || g_ui_present_serial-st->bitmap_present>2) continue;
            /* Match the position actually rendered, not a newer input-thread
               position that has not reached the screen yet. */
            ox=st->pos_x; oy=st->pos_y;
        } else if(!owner_submit_window_position(st->object_ptr,st,&ox,&oy,0)) continue;
        local=st->input_local_bbox;
        /* A full-screen native map still owns its input at its draw order.
           Omitting it lets scaled HUD regions behind it distort map hover. */
        native_size=g_owner_bitmap_hooks_installed && s_equal(st->class_name,"UIRoMapWnd") &&
                    !g_ui_scale_global && rect_is_global(&st->frame_bbox);
        if(local.l>=-4.0f && local.l<=24.0f) local.l=0.0f;
        if(local.t>=-4.0f && local.t<=24.0f) local.t=0.0f;
        if(local.r-local.l<32.0f || local.b-local.t<24.0f) continue;
        if(local.r-local.l>((native_size || (g_ui_keep_on_screen && g_owner_bitmap_hooks_installed))?8192.0f:2048.0f) ||
           local.b-local.t>((native_size || (g_ui_keep_on_screen && g_owner_bitmap_hooks_installed))?8192.0f:2048.0f)) continue;
        src.l=local.l+(float)ox; src.r=local.r+(float)ox;
        src.t=local.t+(float)oy; src.b=local.b+(float)oy;
        /* A fitted bitmap can have an offscreen native origin. Its copied
           display transform, rather than that old origin, owns hit testing. */
        if(!(g_ui_keep_on_screen && g_owner_bitmap_hooks_installed) &&
           (src.r < -256.0f || src.b < -256.0f || src.l > (float)g_ui_screen_w+256.0f || src.t > (float)g_ui_screen_h+256.0f)) continue;
        if(st->last_draw_present) {
            draw_age=g_ui_present_serial>=st->last_draw_present ? g_ui_present_serial-st->last_draw_present : 0;
            if(draw_age<=g_owner_input_exact_max_age_presents) exact_order=st->last_draw_order;
        }
        g_owner_input_regions[rn].rect=src;
        g_owner_input_regions[rn].ax=st->ax;
        g_owner_input_regions[rn].ay=st->ay;
        g_owner_input_regions[rn].fit_scale=st->fit_scale;
        g_owner_input_regions[rn].offset_x=st->offset_x;
        g_owner_input_regions[rn].offset_y=st->offset_y;
        g_owner_input_regions[rn].object_ptr=st->object_ptr;
        g_owner_input_regions[rn].present=g_ui_present_serial;
        g_owner_input_regions[rn].input_order=st->last_input_order;
        g_owner_input_regions[rn].exact_order=exact_order;
        g_owner_input_regions[rn].vtable_ptr=st->vtable_ptr;
        g_owner_input_regions[rn].native_size=native_size;
        ++rn;
        if(manager_active) ++manager_regions; else ++grace_regions;
    }
    g_owner_input_region_count=rn;
    g_owner_input_manager_regions=manager_regions;
    g_owner_input_grace_regions=grace_regions;
    if(rn>g_owner_input_region_peak) g_owner_input_region_peak=rn;
    if(manager_regions>g_owner_input_manager_peak) g_owner_input_manager_peak=manager_regions;
    owner_input_region_unlock();

    for(i=0;i<g_owner_frame_member_count && n<MAX_OWNER_MEMBERS;++i) g_owner_prev_members[n++]=g_owner_frame_members[i];
    g_owner_prev_member_count=n; g_owner_frame_member_count=0;
}

static int owner_input_select_region(const POINT* p, OwnerInputRegion* out, DWORD* count) {
    DWORD i,best_input=0,best_exact=0,candidates=0; float px,py,best_area=1.0e30f;
    int found=0,best_has_exact=0;
    if(count) *count=0;
    if(!p || !out) return 0;
    px=(float)p->x; py=(float)p->y;
    owner_input_region_lock();
    for(i=0;i<g_owner_input_region_count;++i) {
        OwnerInputRegion* m=&g_owner_input_regions[i]; UIRectF dst; float area; int has_exact;
        if(g_ui_present_serial-m->present>2) continue;
        owner_input_region_bounds(m,&dst);
        if(!rect_contains_point(&dst,px,py)) continue;
        ++candidates; area=rect_area(&dst); has_exact=m->exact_order?1:0;
        /* Preserve the same visual ordering for both coordinate conversion
           and the later native root-window hit query. */
        if(!found ||
           (has_exact && !best_has_exact) ||
           (has_exact==best_has_exact && has_exact && m->exact_order>best_exact) ||
           (has_exact==best_has_exact && (!has_exact || m->exact_order==best_exact) && m->input_order>best_input) ||
           (has_exact==best_has_exact && m->exact_order==best_exact && m->input_order==best_input && area<best_area)) {
            found=1; best_has_exact=has_exact; best_exact=m->exact_order; best_input=m->input_order;
            best_area=area; *out=*m;
        }
    }
    owner_input_region_unlock();
    if(count) *count=candidates;
    return found;
}

static int remap_owner_point_selected(POINT* p, OwnerHitSelection* hit) {
    DWORD captured,candidates=0; OwnerInputRegion best; POINT raw;
    if(hit) hit->valid=0;
    if(!p || !g_owner_input_remap_enabled || !g_owner_scale_enabled ||
       !g_input_enabled || !g_input_runtime_enabled || !g_ui_runtime_enabled) {
        owner_input_region_lock(); g_owner_capture_object=0; g_owner_capture_root=0;
        g_owner_capture_native_size=0; owner_input_region_unlock();
        return 0;
    }
    captured=owner_native_capture();
    if(owner_input_map_capture(p,captured)) return 1;
    /* Native capture stays exclusive and does not use the root hit filter. */
    if(captured) return 1;
    raw=*p;
    if(!owner_input_select_region(p,&best,&candidates)) return 0;
    g_owner_input_candidates+=candidates;
    if(candidates>1) ++g_owner_input_overlap_hits;
    if(!owner_input_map_region(p,&best)) return 0;
    if(hit) {
        hit->region=best; hit->raw=raw; hit->mapped=*p;
        hit->thread=g_GetCurrentThreadId?g_GetCurrentThreadId():0;
        hit->valid=hit->thread!=0;
    }
    ++g_owner_mapped_mouse;
    return 1;
}
static int remap_owner_point(POINT* p) {
    return remap_owner_point_selected(p,0);
}

static void owner_hit_publish(const OwnerHitSelection* hit) {
    owner_input_region_lock();
    g_owner_hit_selection=*hit;
    owner_input_region_unlock();
}
static int owner_hit_prepare_scope(LONG x, LONG y, OwnerHitScope* scope) {
    OwnerHitSelection hit; OwnerInputRegion current; POINT mapped; DWORD thread;
    scope->valid=0;
    if(!g_owner_hit_hooks_installed || !g_owner_input_remap_enabled || !g_owner_scale_enabled ||
       !g_input_enabled || !g_input_runtime_enabled || !g_ui_runtime_enabled ||
       !g_GetCurrentThreadId || owner_native_capture()) return 0;
    thread=g_GetCurrentThreadId();
    owner_input_region_lock(); hit=g_owner_hit_selection; owner_input_region_unlock();
    if(!hit.valid || hit.thread!=thread || hit.mapped.x!=x || hit.mapped.y!=y) return 0;
    /* Mouse-down can reuse a sample without another WM_MOUSEMOVE. Expiring or
       consuming the sample here would reintroduce missed stationary clicks.
       Instead revalidate its target against the fresh copied visual snapshot. */
    if(!owner_input_select_region(&hit.raw,&current,0)) {
        /* A miss in displayed UI must also stay a miss for known roots at
           their old native rectangles. Unknown native windows still pass. */
        if(hit.region.object_ptr) return 0;
        scope->target=0; scope->vtable_ptr=0; scope->thread=thread;
        scope->x=x; scope->y=y; scope->valid=1; return 1;
    }
    if(current.object_ptr!=hit.region.object_ptr || current.vtable_ptr!=hit.region.vtable_ptr) return 0;
    if(ui_scale_factor()==1.0f && (current.fit_scale==0.0f || current.fit_scale==1.0f) &&
       current.offset_x==0.0f && current.offset_y==0.0f) return 0;
    /* This is only an identity check before native dispatch. Bounds and input
       ownership still come from copied records, never a live tree walk. */
    if(!mem_readable((void*)(ULONG_PTR)current.object_ptr,4) ||
       *(DWORD*)(ULONG_PTR)current.object_ptr!=current.vtable_ptr) return 0;
    mapped=hit.raw;
    if(!owner_input_map_region(&mapped,&current)) return 0;
    if(mapped.x!=x || mapped.y!=y) return 0;
    scope->target=current.object_ptr; scope->vtable_ptr=current.vtable_ptr;
    scope->thread=thread; scope->x=x; scope->y=y; scope->valid=1;
    return 1;
}
static DWORD __attribute__((thiscall)) owner_hit_query_scoped(void* self, LONG x, LONG y) {
    OwnerHitScope saved,next={0}; DWORD rv=0;
    ++g_owner_hit_queries;
    if(owner_hit_prepare_scope(x,y,&next)) ++g_owner_hit_scoped;
    else ++g_owner_hit_unmatched;
    owner_input_region_lock(); saved=g_owner_hit_scope; g_owner_hit_scope=next; owner_input_region_unlock();
    if(g_owner_hit_query) rv=g_owner_hit_query(self,x,y);
    owner_input_region_lock(); g_owner_hit_scope=saved; owner_input_region_unlock();
    return rv;
}
static int owner_hit_reject_candidate(DWORD obj, DWORD vt, LONG x, LONG y) {
    DWORD i; int reject=0; OwnerHitScope scope;
    owner_input_region_lock(); scope=g_owner_hit_scope; owner_input_region_unlock();
    if(!scope.valid || !g_GetCurrentThreadId || scope.thread!=g_GetCurrentThreadId() ||
       scope.x!=x || scope.y!=y || obj==scope.target) return 0;
    /* Only filter a current, identified root owned by our visual snapshot.
       Unknown windows and native modal/child/capture logic keep their rules. */
    owner_input_region_lock();
    for(i=0;i<g_owner_input_region_count;++i) {
        OwnerInputRegion* r=&g_owner_input_regions[i];
        if(r->object_ptr==obj && r->vtable_ptr==vt && g_ui_present_serial-r->present<=2) {
            reject=1; break;
        }
    }
    owner_input_region_unlock();
    if(reject) ++g_owner_hit_rejected;
    return reject;
}
static DWORD __attribute__((thiscall)) owner_hit_candidate(void* self, LONG x, LONG y) {
    void** vt; PFN_UIHit original;
    if(!self || !mem_readable(self,4)) return 0;
    vt=*(void***)self;
    if(!vt || !mem_readable((BYTE*)vt+0xb8,4)) return 0;
    original=(PFN_UIHit)vt[0xb8/4];
    if(owner_hit_reject_candidate((DWORD)(ULONG_PTR)self,(DWORD)(ULONG_PTR)vt,x,y)) return 0;
    return original?original(self,x,y):0;
}
static int owner_hit_candidate_span_valid(void) {
    BYTE* p;
    if(!g_exe || g_exe_size<PRM_UI_HIT_CANDIDATE_RVA+6) return 0;
    p=(BYTE*)g_exe+PRM_UI_HIT_CANDIDATE_RVA;
    return p[0]==0xff && p[1]==0x90 && p[2]==0xb8 && !p[3] && !p[4] && !p[5];
}
static int owner_hit_patch_candidate(void) {
    BYTE* p=(BYTE*)g_exe+PRM_UI_HIT_CANDIDATE_RVA; DWORD oldp=0,tmp=0;
    if(!owner_hit_candidate_span_valid() || !g_VirtualProtect || !g_FlushInstructionCache ||
       !g_VirtualProtect(p,6,PAGE_EXECUTE_READWRITE,&oldp)) return 0;
    p[0]=0xe8; *(DWORD*)(p+1)=(DWORD)((BYTE*)owner_hit_candidate-(p+5)); p[5]=0x90;
    g_FlushInstructionCache((HANDLE)(ULONG_PTR)-1,p,6);
    g_VirtualProtect(p,6,oldp,&tmp);
    return 1;
}
static void install_owner_hit_hooks(void) {
    BYTE* base=(BYTE*)g_exe;
    if(!g_owner_bitmap_hooks_installed || g_owner_hit_hooks_installed) return;
    if(!g_GetCurrentThreadId || !g_FlushInstructionCache || !owner_hit_candidate_span_valid() ||
       !validated_rel_call(PRM_UI_HIT_EVENT_CALL_RVA,PRM_UI_HIT_EVENT_TARGET_RVA) ||
       !validated_rel_call(PRM_UI_HIT_MOUSE_CALL_RVA,PRM_UI_HIT_MOUSE_TARGET_RVA)) {
        log_line("OwnerHit hooks: opcode/target/API mismatch"); return;
    }
    g_owner_hit_query=(PFN_UIHit)(base+PRM_UI_HIT_EVENT_TARGET_RVA);
    if(owner_hit_patch_candidate() &&
       owner_submit_patch_rel_call(base+PRM_UI_HIT_EVENT_CALL_RVA,(void*)owner_hit_query_scoped) &&
       owner_submit_patch_rel_call(base+PRM_UI_HIT_MOUSE_CALL_RVA,(void*)owner_hit_query_scoped)) {
        g_owner_hit_hooks_installed=1;
        log_line("OwnerHit hooks: OK query=2 candidate=1");
    } else log_line("OwnerHit hooks: patch failed; selection filter disabled");
}

static DWORD owner_submit_hist_sum(DWORD first, DWORD last) {
    DWORD i,sum=0; if(last>=OWNER_AGE_HIST_BINS) last=OWNER_AGE_HIST_BINS-1;
    for(i=first;i<=last;++i) sum+=g_owner_submit_age_hist[i];
    return sum;
}

static void owner_submit_log_age_hist(void) {
    char line[384];
    line[0]=0; s_append(line,sizeof(line)," matchAgeHist 0-3="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(0,3));
    s_append(line,sizeof(line)," 4-7="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(4,7));
    s_append(line,sizeof(line)," 8-11="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(8,11));
    s_append(line,sizeof(line)," 12-15="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(12,15));
    s_append(line,sizeof(line)," 16-23="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(16,23));
    s_append(line,sizeof(line)," 24-31="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(24,31));
    s_append(line,sizeof(line)," 32-47="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(32,47));
    s_append(line,sizeof(line)," 48-63="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(48,63));
    s_append(line,sizeof(line)," 64-79="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(64,79));
    s_append(line,sizeof(line)," 80-95="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(80,95));
    s_append(line,sizeof(line)," 96+="); s_append_uint(line,sizeof(line),owner_submit_hist_sum(96,OWNER_AGE_HIST_BINS-1));
    log_line(line);
}

static void maybe_dump_owner_windows(void) {
    short k; DWORD i,nactive=0,npopup=0; char line[512];
    static OwnerInputRegion active[64];
    if(!g_owner_submit_enabled) return;
    if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_OWNER_DIAGNOSTICS); if(!(k&1)) return;
    line[0]=0; s_append(line,sizeof(line),"OWNER INPUT 3B present="); s_append_uint(line,sizeof(line),g_ui_present_serial);
    s_append(line,sizeof(line)," pending="); s_append_uint(line,sizeof(line),g_owner_submit_count);
    s_append(line,sizeof(line)," tagged="); s_append_uint(line,sizeof(line),g_owner_tagged_draws);
    s_append(line,sizeof(line)," ownerMouse="); s_append_uint(line,sizeof(line),g_owner_mapped_mouse);
    s_append(line,sizeof(line)," fallbackMouse="); s_append_uint(line,sizeof(line),g_ui_mapped_mouse);
    s_append(line,sizeof(line)," ownerRegions="); s_append_uint(line,sizeof(line),g_owner_input_region_count);
    s_append(line,sizeof(line)," managerRegions="); s_append_uint(line,sizeof(line),g_owner_input_manager_regions);
    s_append(line,sizeof(line)," graceRegions="); s_append_uint(line,sizeof(line),g_owner_input_grace_regions);
    s_append(line,sizeof(line)," ownerCandidates="); s_append_uint(line,sizeof(line),g_owner_input_candidates);
    s_append(line,sizeof(line)," ownerOverlaps="); s_append_uint(line,sizeof(line),g_owner_input_overlap_hits); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," UISettings scale="); s_append_uint(line,sizeof(line),(DWORD)g_ui_scale_percent);
    s_append(line,sizeof(line)," enabled="); s_append_uint(line,sizeof(line),(DWORD)g_ui_runtime_enabled);
    s_append(line,sizeof(line)," keepOnScreen="); s_append_uint(line,sizeof(line),(DWORD)g_ui_keep_on_screen);
    s_append(line,sizeof(line)," screen="); s_append_int(line,sizeof(line),g_ui_screen_w);
    s_append(line,sizeof(line),"x"); s_append_int(line,sizeof(line),g_ui_screen_h); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," totals scopedCalls="); s_append_uint(line,sizeof(line),g_owner_submit_scoped_calls);
    s_append(line,sizeof(line)," matched="); s_append_uint(line,sizeof(line),g_owner_submit_total_matched);
    s_append(line,sizeof(line)," ambiguous="); s_append_uint(line,sizeof(line),g_owner_submit_total_ambiguous);
    s_append(line,sizeof(line)," expired="); s_append_uint(line,sizeof(line),g_owner_submit_total_expired);
    s_append(line,sizeof(line)," peakPending="); s_append_uint(line,sizeof(line),g_owner_submit_peak_pending);
    s_append(line,sizeof(line)," overflow="); s_append_uint(line,sizeof(line),g_owner_submit_total_overflow);
    s_append(line,sizeof(line)," maxMatchAge="); s_append_uint(line,sizeof(line),g_owner_submit_match_age_max);
    s_append(line,sizeof(line)," posInvalid="); s_append_uint(line,sizeof(line),g_owner_submit_pos_invalid);
    s_append(line,sizeof(line)," posUnreadable="); s_append_uint(line,sizeof(line),g_owner_submit_pos_unreadable);
    s_append(line,sizeof(line)," posRange="); s_append_uint(line,sizeof(line),g_owner_submit_pos_range);
    s_append(line,sizeof(line)," regionPeak="); s_append_uint(line,sizeof(line),g_owner_input_region_peak);
    s_append(line,sizeof(line)," managerPeak="); s_append_uint(line,sizeof(line),g_owner_input_manager_peak); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," WorldInput enabled="); s_append_uint(line,sizeof(line),(DWORD)g_world_input_enabled);
    s_append(line,sizeof(line)," calls="); s_append_uint(line,sizeof(line),g_world_input_calls);
    s_append(line,sizeof(line)," rawUses="); s_append_uint(line,sizeof(line),g_world_input_raw_uses);
    s_append(line,sizeof(line)," normalized="); s_append_uint(line,sizeof(line),g_world_input_normalized);
    s_append(line,sizeof(line)," rawFailures="); s_append_uint(line,sizeof(line),g_world_input_raw_failures);
    s_append(line,sizeof(line)," viewport="); s_append_int(line,sizeof(line),g_world_input_view_w);
    s_append(line,sizeof(line),"x"); s_append_int(line,sizeof(line),g_world_input_view_h);
    s_append(line,sizeof(line)," client="); s_append_int(line,sizeof(line),g_world_input_client_w);
    s_append(line,sizeof(line),"x"); s_append_int(line,sizeof(line),g_world_input_client_h);
    s_append(line,sizeof(line)," raw="); s_append_int(line,sizeof(line),g_world_raw_x);
    s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),g_world_raw_y);
    s_append(line,sizeof(line)," mapped="); s_append_int(line,sizeof(line),g_world_mapped_x);
    s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),g_world_mapped_y);
    s_append(line,sizeof(line)," maxDelta="); s_append_uint(line,sizeof(line),g_world_input_max_delta); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," Cursor hooks="); s_append_uint(line,sizeof(line),(DWORD)g_cursor_hooks_installed);
    s_append(line,sizeof(line)," calls="); s_append_uint(line,sizeof(line),g_cursor_calls);
    s_append(line,sizeof(line)," rawUses="); s_append_uint(line,sizeof(line),g_cursor_raw_uses);
    s_append(line,sizeof(line)," rawFailures="); s_append_uint(line,sizeof(line),g_cursor_raw_failures);
    s_append(line,sizeof(line)," submits="); s_append_uint(line,sizeof(line),g_cursor_submits);
    s_append(line,sizeof(line)," bypassed="); s_append_uint(line,sizeof(line),g_cursor_bypassed);
    s_append(line,sizeof(line)," expired="); s_append_uint(line,sizeof(line),g_cursor_expired);
    s_append(line,sizeof(line)," mismatched="); s_append_uint(line,sizeof(line),g_cursor_mismatched);
    s_append(line,sizeof(line)," overflow="); s_append_uint(line,sizeof(line),g_cursor_overflow);
    s_append(line,sizeof(line)," peak="); s_append_uint(line,sizeof(line),g_cursor_peak); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," OwnerBitmap hooks="); s_append_uint(line,sizeof(line),(DWORD)g_owner_bitmap_hooks_installed);
    s_append(line,sizeof(line)," calls="); s_append_uint(line,sizeof(line),g_owner_bitmap_calls);
    s_append(line,sizeof(line)," submits="); s_append_uint(line,sizeof(line),g_owner_bitmap_submits);
    s_append(line,sizeof(line)," matched="); s_append_uint(line,sizeof(line),g_owner_bitmap_matched);
    s_append(line,sizeof(line)," pending="); s_append_uint(line,sizeof(line),g_owner_bitmap_active_count);
    s_append(line,sizeof(line)," peak="); s_append_uint(line,sizeof(line),g_owner_bitmap_peak);
    s_append(line,sizeof(line)," overflow="); s_append_uint(line,sizeof(line),g_owner_bitmap_overflow);
    s_append(line,sizeof(line)," expired="); s_append_uint(line,sizeof(line),g_owner_bitmap_expired);
    s_append(line,sizeof(line)," mismatched="); s_append_uint(line,sizeof(line),g_owner_bitmap_mismatched);
    s_append(line,sizeof(line)," unsupported="); s_append_uint(line,sizeof(line),g_owner_bitmap_unsupported);
    s_append(line,sizeof(line)," offscreen="); s_append_uint(line,sizeof(line),g_owner_bitmap_offscreen);
    s_append(line,sizeof(line)," unowned="); s_append_uint(line,sizeof(line),g_owner_bitmap_unowned); log_line(line);
    log_uint(" MapOverlay draws=",g_owner_map_draws);
    log_uint(" Minimap draws=",g_owner_minimap_draws);
    line[0]=0; s_append(line,sizeof(line)," OwnerHit hooks="); s_append_uint(line,sizeof(line),(DWORD)g_owner_hit_hooks_installed);
    s_append(line,sizeof(line)," queries="); s_append_uint(line,sizeof(line),g_owner_hit_queries);
    s_append(line,sizeof(line)," scoped="); s_append_uint(line,sizeof(line),g_owner_hit_scoped);
    s_append(line,sizeof(line)," rejected="); s_append_uint(line,sizeof(line),g_owner_hit_rejected);
    s_append(line,sizeof(line)," unmatched="); s_append_uint(line,sizeof(line),g_owner_hit_unmatched); log_line(line);

    line[0]=0; s_append(line,sizeof(line)," UIFilter crisp="); s_append_uint(line,sizeof(line),(DWORD)g_ui_sharp_filter);
    s_append(line,sizeof(line)," draws="); s_append_uint(line,sizeof(line),g_ui_sharp_draws);
    s_append(line,sizeof(line)," failures="); s_append_uint(line,sizeof(line),g_ui_sharp_failures); log_line(line);
    line[0]=0; s_append(line,sizeof(line)," OwnerCapture maps="); s_append_uint(line,sizeof(line),g_owner_capture_maps);
    s_append(line,sizeof(line)," changes="); s_append_uint(line,sizeof(line),g_owner_capture_changes);
    s_append(line,sizeof(line)," unknown="); s_append_uint(line,sizeof(line),g_owner_capture_unknown);
    s_append(line,sizeof(line)," links="); s_append_uint(line,sizeof(line),g_owner_capture_link_count);
    s_append(line,sizeof(line)," overflow="); s_append_uint(line,sizeof(line),g_owner_capture_link_overflow);
    s_append(line,sizeof(line)," capacityLimits="); s_append_uint(line,sizeof(line),g_owner_capture_capacity_limits);
    s_append(line,sizeof(line)," walkLimits="); s_append_uint(line,sizeof(line),g_owner_capture_walk_limits);
    s_append(line,sizeof(line)," staleRoots="); s_append_uint(line,sizeof(line),g_owner_capture_stale_roots);
    s_append(line,sizeof(line)," peak="); s_append_uint(line,sizeof(line),g_owner_capture_link_peak);
    s_append(line,sizeof(line)," object="); s_append_hex8(line,sizeof(line),g_owner_capture_object);
    s_append(line,sizeof(line)," root="); s_append_hex8(line,sizeof(line),g_owner_capture_root); log_line(line);
    if(g_owner_submit_pos_invalid) {
        line[0]=0; s_append(line,sizeof(line)," invalidLast reason="); s_append_uint(line,sizeof(line),g_owner_submit_pos_last_reason);
        s_append(line,sizeof(line)," obj="); s_append_hex8(line,sizeof(line),g_owner_submit_pos_last_obj);
        s_append(line,sizeof(line)," pos="); s_append_int(line,sizeof(line),g_owner_submit_pos_last_x);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),g_owner_submit_pos_last_y); log_line(line);
    }
    owner_input_region_lock();
    nactive=g_owner_input_region_count<64?g_owner_input_region_count:64;
    for(i=0;i<nactive;++i) active[i]=g_owner_input_regions[i];
    owner_input_region_unlock();
    for(i=0;i<nactive;++i) {
        UIRectF screen; OwnerWindowState* st=owner_state_for(active[i].object_ptr,0); if(!st) continue;
        owner_input_region_bounds(&active[i],&screen);
        line[0]=0; s_append(line,sizeof(line)," owner obj="); s_append_hex8(line,sizeof(line),st->object_ptr);
        s_append(line,sizeof(line)," class="); s_append(line,sizeof(line),st->class_name);
        s_append(line,sizeof(line)," pos="); s_append_int(line,sizeof(line),st->pos_x); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),st->pos_y);
        s_append(line,sizeof(line)," anchor="); s_append_int(line,sizeof(line),(LONG)st->ax); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)st->ay);
        if(st->have_input_local_bbox) { s_append(line,sizeof(line)," local="); s_append_int(line,sizeof(line),(LONG)st->input_local_bbox.l); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)st->input_local_bbox.t); s_append(line,sizeof(line),".."); s_append_int(line,sizeof(line),(LONG)st->input_local_bbox.r); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)st->input_local_bbox.b); }
        s_append(line,sizeof(line)," inputOrder="); s_append_uint(line,sizeof(line),st->last_input_order);
        s_append(line,sizeof(line)," nativeSize="); s_append_uint(line,sizeof(line),(DWORD)active[i].native_size);
        s_append(line,sizeof(line)," fitPercent="); s_append_uint(line,sizeof(line),(DWORD)(active[i].fit_scale*100.0f+0.5f));
        s_append(line,sizeof(line)," offset="); s_append_int(line,sizeof(line),(LONG)active[i].offset_x);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)active[i].offset_y);
        s_append(line,sizeof(line)," display="); s_append_int(line,sizeof(line),(LONG)screen.l);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)screen.t);
        s_append(line,sizeof(line),".."); s_append_int(line,sizeof(line),(LONG)screen.r);
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)screen.b);
        s_append(line,sizeof(line)," inputLast="); s_append_uint(line,sizeof(line),st->last_input_present);
        s_append(line,sizeof(line)," drawOrder="); s_append_uint(line,sizeof(line),st->last_draw_order);
        s_append(line,sizeof(line)," drawLast="); s_append_uint(line,sizeof(line),st->last_draw_present);
        s_append(line,sizeof(line)," last="); s_append_uint(line,sizeof(line),st->last_present); log_line(line);
    }
    for(i=0;i<g_owner_window_count && npopup<32;++i) {
        OwnerWindowState* st=&g_owner_windows[i]; DWORD age;
        if(!owner_class_is_hover_popup(st->class_name) && !owner_class_is_world_label(st->class_name) &&
           !owner_class_is_world_name(st->class_name)) continue;
        age=g_ui_present_serial>=st->last_present?g_ui_present_serial-st->last_present:0;
        if(!st->last_present || age>g_owner_submit_max_age_presents) continue;
        line[0]=0; s_append(line,sizeof(line)," visualOnly obj="); s_append_hex8(line,sizeof(line),st->object_ptr);
        s_append(line,sizeof(line)," class="); s_append(line,sizeof(line),st->class_name);
        s_append(line,sizeof(line)," pos="); s_append_int(line,sizeof(line),st->pos_x); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),st->pos_y);
        s_append(line,sizeof(line)," anchor="); s_append_int(line,sizeof(line),(LONG)st->ax); s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)st->ay);
        s_append(line,sizeof(line)," size="); s_append_int(line,sizeof(line),(LONG)(st->input_local_bbox.r-st->input_local_bbox.l));
        s_append(line,sizeof(line),","); s_append_int(line,sizeof(line),(LONG)(st->input_local_bbox.b-st->input_local_bbox.t));
        s_append(line,sizeof(line)," drawLast="); s_append_uint(line,sizeof(line),st->last_draw_present);
        s_append(line,sizeof(line)," inputOrder="); s_append_uint(line,sizeof(line),st->last_input_order);
        s_append(line,sizeof(line)," age="); s_append_uint(line,sizeof(line),age); log_line(line); ++npopup;
    }
}



/* ---------- Phase 2I virtual-slot + deferred-submit tracing ----------
 *
 * Phase 2H proved that RTTI/vtable discovery is correct, but slot 17 did not
 * bracket the final D3D7 calls because this client appears to defer UI
 * rendering: window methods enqueue sprites/rects and the renderer flushes
 * them later.  Phase 2I therefore traces a safe range of real virtual slots
 * with transparent x86 return trampolines and also counts three candidate UI
 * submission helpers while each slot is active.  F8 starts a 2-second
 * capture.  The 2F visual scaler remains the playable fallback.
 */
#define VTRACE_SLOT_COUNT 40
#define VTRACE_MAX_CLASSES 8
#define VTRACE_MAX_DEPTH 128

typedef struct {
    void** vt;
    DWORD vt_rva;
    char class_name[72];
    void* original[VTRACE_SLOT_COUNT];
    DWORD calls[VTRACE_SLOT_COUNT];
    DWORD submit0[VTRACE_SLOT_COUNT];
    DWORD submit1[VTRACE_SLOT_COUNT];
    DWORD submit2[VTRACE_SLOT_COUNT];
    DWORD d3d_ui[VTRACE_SLOT_COUNT];
} VTraceClass;

typedef struct {
    DWORD return_addr;
    DWORD prev_class;
    DWORD prev_slot;
    DWORD prev_self;
} VTraceFrame;

static VTraceClass g_vtrace_classes[VTRACE_MAX_CLASSES];
static DWORD g_vtrace_class_count;
static VTraceFrame g_vtrace_stack[VTRACE_MAX_DEPTH];
static DWORD g_vtrace_depth;
static DWORD g_vtrace_current_class=0xffffffffUL;
static DWORD g_vtrace_current_slot=0xffffffffUL;
static DWORD g_vtrace_current_self;
static int g_vtrace_enabled=1;
static DWORD g_vtrace_capture_ms=2000;
static DWORD g_vtrace_slot_first=0;
static DWORD g_vtrace_slot_last=39;
static int g_vtrace_capture_active;
static DWORD g_vtrace_capture_until;
static DWORD g_vtrace_capture_serial;
static int g_vtrace_submit_hooks_installed;
static int g_vtrace_overflow_logged;

/* Globals intentionally exported to the companion assembly thunks. */
DWORD g_vtrace_asm_slot;
DWORD g_vtrace_asm_self;
DWORD g_vtrace_asm_ret;
void* g_vtrace_asm_jump;
DWORD g_vtrace_asm_return;
void* g_vtrace_submit0_continue;
void* g_vtrace_submit1_target;
void* g_vtrace_submit2_continue;

extern void vtrace_slot_0(void);
extern void vtrace_slot_1(void);
extern void vtrace_slot_2(void);
extern void vtrace_slot_3(void);
extern void vtrace_slot_4(void);
extern void vtrace_slot_5(void);
extern void vtrace_slot_6(void);
extern void vtrace_slot_7(void);
extern void vtrace_slot_8(void);
extern void vtrace_slot_9(void);
extern void vtrace_slot_10(void);
extern void vtrace_slot_11(void);
extern void vtrace_slot_12(void);
extern void vtrace_slot_13(void);
extern void vtrace_slot_14(void);
extern void vtrace_slot_15(void);
extern void vtrace_slot_16(void);
extern void vtrace_slot_17(void);
extern void vtrace_slot_18(void);
extern void vtrace_slot_19(void);
extern void vtrace_slot_20(void);
extern void vtrace_slot_21(void);
extern void vtrace_slot_22(void);
extern void vtrace_slot_23(void);
extern void vtrace_slot_24(void);
extern void vtrace_slot_25(void);
extern void vtrace_slot_26(void);
extern void vtrace_slot_27(void);
extern void vtrace_slot_28(void);
extern void vtrace_slot_29(void);
extern void vtrace_slot_30(void);
extern void vtrace_slot_31(void);
extern void vtrace_slot_32(void);
extern void vtrace_slot_33(void);
extern void vtrace_slot_34(void);
extern void vtrace_slot_35(void);
extern void vtrace_slot_36(void);
extern void vtrace_slot_37(void);
extern void vtrace_slot_38(void);
extern void vtrace_slot_39(void);
extern void vtrace_submit0_thunk(void);
extern void vtrace_submit1_thunk(void);
extern void vtrace_submit2_thunk(void);

static void* g_vtrace_slot_thunks[VTRACE_SLOT_COUNT]={
    (void*)vtrace_slot_0,
    (void*)vtrace_slot_1,
    (void*)vtrace_slot_2,
    (void*)vtrace_slot_3,
    (void*)vtrace_slot_4,
    (void*)vtrace_slot_5,
    (void*)vtrace_slot_6,
    (void*)vtrace_slot_7,
    (void*)vtrace_slot_8,
    (void*)vtrace_slot_9,
    (void*)vtrace_slot_10,
    (void*)vtrace_slot_11,
    (void*)vtrace_slot_12,
    (void*)vtrace_slot_13,
    (void*)vtrace_slot_14,
    (void*)vtrace_slot_15,
    (void*)vtrace_slot_16,
    (void*)vtrace_slot_17,
    (void*)vtrace_slot_18,
    (void*)vtrace_slot_19,
    (void*)vtrace_slot_20,
    (void*)vtrace_slot_21,
    (void*)vtrace_slot_22,
    (void*)vtrace_slot_23,
    (void*)vtrace_slot_24,
    (void*)vtrace_slot_25,
    (void*)vtrace_slot_26,
    (void*)vtrace_slot_27,
    (void*)vtrace_slot_28,
    (void*)vtrace_slot_29,
    (void*)vtrace_slot_30,
    (void*)vtrace_slot_31,
    (void*)vtrace_slot_32,
    (void*)vtrace_slot_33,
    (void*)vtrace_slot_34,
    (void*)vtrace_slot_35,
    (void*)vtrace_slot_36,
    (void*)vtrace_slot_37,
    (void*)vtrace_slot_38,
    (void*)vtrace_slot_39
};

static int vtrace_target_class(const char* n) {
    return s_equal(n,"UIItemWnd") || s_equal(n,"UIStatusWnd") || s_equal(n,"UINewSkillListWnd");
}

static VTraceClass* vtrace_class_for_vt(void** vt, DWORD* index_out) {
    DWORD i;
    for(i=0;i<g_vtrace_class_count;++i) if(g_vtrace_classes[i].vt==vt) { if(index_out)*index_out=i; return &g_vtrace_classes[i]; }
    return 0;
}

static void vtrace_reset_counts(void) {
    DWORD i,j;
    for(i=0;i<g_vtrace_class_count;++i) for(j=0;j<VTRACE_SLOT_COUNT;++j) {
        g_vtrace_classes[i].calls[j]=0; g_vtrace_classes[i].submit0[j]=0; g_vtrace_classes[i].submit1[j]=0;
        g_vtrace_classes[i].submit2[j]=0; g_vtrace_classes[i].d3d_ui[j]=0;
    }
}

/* Transparent virtual-call entry/exit. The assembly wrapper does not know the
 * signature: it only swaps the return address, so arbitrary stack arguments
 * and callee-pop RET n semantics are preserved. */
void WINAPI vtrace_enter_c(void) {
    void** vt=0; VTraceClass* c=0; DWORD ci=0,slot=g_vtrace_asm_slot;
    g_vtrace_asm_jump=0;
    if(g_vtrace_asm_self && mem_readable((void*)g_vtrace_asm_self,4)) vt=*(void***)g_vtrace_asm_self;
    c=vtrace_class_for_vt(vt,&ci);
    if(!c || slot>=VTRACE_SLOT_COUNT || !c->original[slot]) return;
    g_vtrace_asm_jump=c->original[slot];
    if(g_vtrace_depth<VTRACE_MAX_DEPTH) {
        VTraceFrame* f=&g_vtrace_stack[g_vtrace_depth++];
        f->return_addr=g_vtrace_asm_ret; f->prev_class=g_vtrace_current_class; f->prev_slot=g_vtrace_current_slot; f->prev_self=g_vtrace_current_self;
        g_vtrace_current_class=ci; g_vtrace_current_slot=slot; g_vtrace_current_self=g_vtrace_asm_self;
        if(g_vtrace_capture_active) ++c->calls[slot];
    } else if(!g_vtrace_overflow_logged) { g_vtrace_overflow_logged=1; log_line("VirtualTrace context stack overflow"); }
}

void WINAPI vtrace_leave_c(void) {
    VTraceFrame* f;
    if(!g_vtrace_depth) { g_vtrace_asm_return=g_vtrace_asm_ret; g_vtrace_current_class=0xffffffffUL; g_vtrace_current_slot=0xffffffffUL; g_vtrace_current_self=0; return; }
    f=&g_vtrace_stack[--g_vtrace_depth];
    g_vtrace_asm_return=f->return_addr; g_vtrace_current_class=f->prev_class; g_vtrace_current_slot=f->prev_slot; g_vtrace_current_self=f->prev_self;
}

static void vtrace_note_submit_kind(int kind) {
    VTraceClass* c; DWORD s=g_vtrace_current_slot;
    if(!g_vtrace_capture_active || g_vtrace_current_class>=g_vtrace_class_count || s>=VTRACE_SLOT_COUNT) return;
    c=&g_vtrace_classes[g_vtrace_current_class];
    if(kind==0) ++c->submit0[s]; else if(kind==1) ++c->submit1[s]; else ++c->submit2[s];
}
void WINAPI vtrace_note_submit0(void) { vtrace_note_submit_kind(0); }
void WINAPI vtrace_note_submit1(void) { vtrace_note_submit_kind(1); }
void WINAPI vtrace_note_submit2(void) { vtrace_note_submit_kind(2); }

static void vtrace_note_d3d_ui(void) {
    DWORD s=g_vtrace_current_slot;
    if(!g_vtrace_capture_active || g_vtrace_current_class>=g_vtrace_class_count || s>=VTRACE_SLOT_COUNT) return;
    ++g_vtrace_classes[g_vtrace_current_class].d3d_ui[s];
}

static int vtrace_patch_rel_jmp(BYTE* at, DWORD nbytes, void* target) {
    DWORD oldp=0,tmp=0,rel; DWORD i;
    if(!at || nbytes<5 || !g_VirtualProtect) return 0;
    rel=(DWORD)((BYTE*)target-(at+5));
    if(!g_VirtualProtect(at,nbytes,PAGE_EXECUTE_READWRITE,&oldp)) return 0;
    at[0]=0xE9; *(DWORD*)(at+1)=rel; for(i=5;i<nbytes;++i) at[i]=0x90;
    if(g_FlushInstructionCache) g_FlushInstructionCache((HANDLE)(ULONG_PTR)-1,at,nbytes);
    g_VirtualProtect(at,nbytes,oldp,&tmp); return 1;
}

static void vtrace_install_submit_hooks(void) {
    BYTE* a; LONG rel; char line[192];
    if(g_vtrace_submit_hooks_installed || !g_vtrace_enabled || !g_exe) return;
    /* RVA 0x71C0B0: prolog 55 8B EC 56 8B 71 24, then sprite/rect submit work. */
    a=(BYTE*)g_exe+0x0071C0B0UL;
    if(mem_readable(a,7) && a[0]==0x55 && a[1]==0x8B && a[2]==0xEC && a[3]==0x56 && a[4]==0x8B && a[5]==0x71 && a[6]==0x24) {
        g_vtrace_submit0_continue=a+7;
        log_line(vtrace_patch_rel_jmp(a,7,(void*)vtrace_submit0_thunk)?"VirtualTrace helper A hook: OK RVA=0x0071C0B0":"VirtualTrace helper A hook: FAILED");
    } else log_line("VirtualTrace helper A hook: signature mismatch");
    /* RVA 0x71C230 is already a 5-byte xDiff JMP; preserve its real target. */
    a=(BYTE*)g_exe+0x0071C230UL;
    if(mem_readable(a,5) && a[0]==0xE9) {
        rel=*(LONG*)(a+1); g_vtrace_submit1_target=a+5+rel;
        log_line(vtrace_patch_rel_jmp(a,5,(void*)vtrace_submit1_thunk)?"VirtualTrace helper B hook: OK RVA=0x0071C230":"VirtualTrace helper B hook: FAILED");
    } else log_line("VirtualTrace helper B hook: signature mismatch");
    /* RVA 0x71C4D0: 55 8B EC 83 EC 38. */
    a=(BYTE*)g_exe+0x0071C4D0UL;
    if(mem_readable(a,6) && a[0]==0x55 && a[1]==0x8B && a[2]==0xEC && a[3]==0x83 && a[4]==0xEC && a[5]==0x38) {
        g_vtrace_submit2_continue=a+6;
        log_line(vtrace_patch_rel_jmp(a,6,(void*)vtrace_submit2_thunk)?"VirtualTrace helper C hook: OK RVA=0x0071C4D0":"VirtualTrace helper C hook: FAILED");
    } else log_line("VirtualTrace helper C hook: signature mismatch");
    g_vtrace_submit_hooks_installed=1; (void)line;
}

static void vtrace_install_vtable(DWORD obj, DWORD vt_rva, const char* name) {
    void** vt; VTraceClass* c; DWORD ci=0,s,fnrva; char line[192];
    if(!g_vtrace_enabled || !obj || !vtrace_target_class(name) || !mem_readable((void*)obj,4)) return;
    vt=*(void***)obj; if(!vt) return;
    c=vtrace_class_for_vt(vt,&ci); if(c) return;
    if(g_vtrace_class_count>=VTRACE_MAX_CLASSES) return;
    c=&g_vtrace_classes[g_vtrace_class_count]; c->vt=vt; c->vt_rva=vt_rva; s_copy(c->class_name,sizeof(c->class_name),name);
    for(s=0;s<VTRACE_SLOT_COUNT;++s) { c->original[s]=0; c->calls[s]=c->submit0[s]=c->submit1[s]=c->submit2[s]=c->d3d_ui[s]=0; }
    ci=g_vtrace_class_count++;
    for(s=g_vtrace_slot_first;s<=g_vtrace_slot_last && s<VTRACE_SLOT_COUNT;++s) {
        void* orig=0; if(!mem_readable(vt+s,4)) continue; fnrva=ptr_to_rva(vt[s]);
        if(fnrva==0xffffffffUL || fnrva>=g_exe_size) continue;
        if(patch_vtable_slot(vt,s,g_vtrace_slot_thunks[s],&orig)) c->original[s]=orig;
    }
    line[0]=0; s_append(line,sizeof(line),"VirtualTrace vtable armed: class="); s_append(line,sizeof(line),name);
    s_append(line,sizeof(line)," vtRVA="); s_append_hex8(line,sizeof(line),vt_rva); s_append(line,sizeof(line)," slots="); s_append_uint(line,sizeof(line),g_vtrace_slot_first);
    s_append(line,sizeof(line),".."); s_append_uint(line,sizeof(line),g_vtrace_slot_last); log_line(line);
}

static void vtrace_install_active_vtables(void) {
    static const DWORD offs[4]={0x174,0x17c,0x184,0x18c}; BYTE* mgr; DWORD k; char name[72]; DWORD vr=0;
    if(!g_vtrace_enabled || !g_exe || g_exe_size<0xab76d8+0x200) return;
    mgr=(BYTE*)g_exe+0xab76d8;
    for(k=0;k<4;++k) {
        DWORD head,node,n=0; if(!mem_readable(mgr+offs[k],4)) continue; head=*(DWORD*)(mgr+offs[k]); if(!mem_readable((void*)head,4)) continue; node=*(DWORD*)head;
        while(node && node!=head && n<192 && mem_readable((void*)node,12)) {
            DWORD obj=*(DWORD*)(node+8); name[0]=0; vr=0; if(rtti_name_from_object(obj,name,sizeof(name),&vr)) vtrace_install_vtable(obj,vr,name);
            node=*(DWORD*)node; ++n;
        }
    }
}

static void vtrace_dump_results(void) {
    DWORD i,s; char line[320];
    line[0]=0; s_append(line,sizeof(line),"--- VIRTUAL TRACE END #"); s_append_uint(line,sizeof(line),g_vtrace_capture_serial); s_append(line,sizeof(line)," ---"); log_line(line);
    for(i=0;i<g_vtrace_class_count;++i) {
        VTraceClass* c=&g_vtrace_classes[i];
        for(s=g_vtrace_slot_first;s<=g_vtrace_slot_last && s<VTRACE_SLOT_COUNT;++s) {
            DWORD total=c->calls[s],a=c->submit0[s],b=c->submit1[s],cc=c->submit2[s],d=c->d3d_ui[s];
            if(!(total||a||b||cc||d) || !c->original[s]) continue;
            line[0]=0; s_append(line,sizeof(line)," class="); s_append(line,sizeof(line),c->class_name);
            s_append(line,sizeof(line)," slot="); s_append_uint(line,sizeof(line),s);
            s_append(line,sizeof(line)," fnRVA="); s_append_hex8(line,sizeof(line),ptr_to_rva(c->original[s]));
            s_append(line,sizeof(line)," calls="); s_append_uint(line,sizeof(line),total);
            s_append(line,sizeof(line)," helperA="); s_append_uint(line,sizeof(line),a);
            s_append(line,sizeof(line)," helperB="); s_append_uint(line,sizeof(line),b);
            s_append(line,sizeof(line)," helperC="); s_append_uint(line,sizeof(line),cc);
            s_append(line,sizeof(line)," directD3DUI="); s_append_uint(line,sizeof(line),d); log_line(line);
        }
    }
    log_line("--- END VIRTUAL TRACE ---");
}

static void vtrace_maybe_finish(void) {
    DWORD now; if(!g_vtrace_capture_active || !g_GetTickCount) return; now=g_GetTickCount();
    if((LONG)(now-g_vtrace_capture_until)>=0) { g_vtrace_capture_active=0; vtrace_dump_results(); }
}

static void vtrace_poll_hotkey(void) {
    short k; char line[160]; DWORD now;
    if(!g_vtrace_enabled || !g_GetAsyncKeyState || !g_GetTickCount) return;
    k=g_GetAsyncKeyState(VK_OWNER_DIAGNOSTICS);
    if((k&1) && !g_vtrace_capture_active) {
        vtrace_install_active_vtables(); vtrace_install_submit_hooks(); vtrace_reset_counts();
        now=g_GetTickCount(); g_vtrace_capture_until=now+g_vtrace_capture_ms; ++g_vtrace_capture_serial; g_vtrace_capture_active=1;
        line[0]=0; s_append(line,sizeof(line),"--- VIRTUAL TRACE START #"); s_append_uint(line,sizeof(line),g_vtrace_capture_serial);
        s_append(line,sizeof(line)," (F8) classes="); s_append_uint(line,sizeof(line),g_vtrace_class_count); s_append(line,sizeof(line)," ---"); log_line(line);
    }
    vtrace_maybe_finish();
}

static void clear_ui_frame_accumulator(void) {
    g_ui_frame_rect_count=0;
    g_owner_bitmap_frame_calls=0;
}

static int group_for_rect_locked(const UIRectF* r);

static void collect_ui_rect(float l,float t,float r,float b) {
    UIRectF q; DWORD i, start;
    if(r<=l || b<=t || g_ui_frame_rect_count>=MAX_UI_FRAME_RECTS) return;
    q.l=l; q.t=t; q.r=r; q.b=b;
    /* Deduplicate the common case where the same exact quad is emitted more
       than once in one scene. Only inspect a short tail to keep this cheap. */
    start = g_ui_frame_rect_count>64 ? g_ui_frame_rect_count-64 : 0;
    for(i=start;i<g_ui_frame_rect_count;++i) {
        UIRectF* x=&g_ui_frame_rects[i];
        if(f_abs(x->l-l)<0.5f && f_abs(x->t-t)<0.5f && f_abs(x->r-r)<0.5f && f_abs(x->b-b)<0.5f) return;
    }
    {
        int gi; DWORD hint=0;
        ui_group_lock();
        gi=group_for_rect_locked(&q);
        if(gi>=0 && (DWORD)gi<g_ui_prev_group_count) hint=g_ui_prev_groups[gi].stable_id;
        ui_group_unlock();
        g_ui_frame_rects[g_ui_frame_rect_count]=q;
        g_ui_frame_rect_hints[g_ui_frame_rect_count]=hint;
        ++g_ui_frame_rect_count;
    }
}

static int group_for_rect_locked(const UIRectF* r) {
    DWORD i; int best=-1, best_contains=-1;
    float best_area=999999999.0f, best_dist=999999999.0f;
    float cx=(r->l+r->r)*0.5f, cy=(r->t+r->b)*0.5f;
    for(i=0;i<g_ui_prev_group_count;++i) {
        UIRectF b; float area,bcx,bcy,dist;
        b.l=g_ui_prev_groups[i].l; b.t=g_ui_prev_groups[i].t; b.r=g_ui_prev_groups[i].r; b.b=g_ui_prev_groups[i].b;
        if(!rect_near(r,&b,(float)g_ui_match_gap)) continue;
        area=rect_area(&b);
        if(rect_contains_point(&b,cx,cy)) {
            if(area<best_area) { best_contains=(int)i; best_area=area; }
            continue;
        }
        bcx=(b.l+b.r)*0.5f; bcy=(b.t+b.b)*0.5f;
        dist=f_abs(cx-bcx)+f_abs(cy-bcy);
        if(dist<best_dist) { best=(int)i; best_dist=dist; }
    }
    return best_contains>=0 ? best_contains : best;
}

static int get_group_transform_for_rect(const UIRectF* r, float* ax, float* ay) {
    int idx;
    ui_group_lock();
    idx=group_for_rect_locked(r);
    if(idx>=0) { *ax=g_ui_prev_groups[idx].ax; *ay=g_ui_prev_groups[idx].ay; }
    ui_group_unlock();
    return idx>=0;
}

static void finalize_ui_frame(void) {
    UIGroup* tmp=g_ui_build_groups;
    UIGroupMember* members=g_ui_build_members;
    DWORD ng=0, i, j, pass;
    DWORD nm=0;
    float gap=(float)g_ui_group_gap;

    /* Seed/expand connected groups. Full-screen-ish primitives are deliberately
       kept out of clustering unless ScaleGlobal is requested; otherwise one
       overlay can glue every independent window into a single mega-group. */
    for(i=0;i<g_ui_frame_rect_count;++i) {
        UIRectF r=g_ui_frame_rects[i]; DWORD hint=g_ui_frame_rect_hints[i];
        int global=rect_is_global(&r), best=-1;
        float best_area=999999999.0f;
        if(global && !g_ui_scale_global) continue;
        for(j=0;j<ng;++j) {
            UIRectF b; float area;
            if(tmp[j].is_global != global) continue;
            if(hint && tmp[j].stable_id && hint!=tmp[j].stable_id) continue;
            b.l=tmp[j].l; b.t=tmp[j].t; b.r=tmp[j].r; b.b=tmp[j].b;
            if(!rect_near(&r,&b,gap)) continue;
            area=rect_area(&b);
            if(area<best_area) { best=(int)j; best_area=area; }
        }
        if(best<0) {
            if(ng>=MAX_UI_GROUPS) continue;
            tmp[ng].l=r.l; tmp[ng].t=r.t; tmp[ng].r=r.r; tmp[ng].b=r.b;
            tmp[ng].ax=0; tmp[ng].ay=0; tmp[ng].is_global=global; tmp[ng].stable_id=hint; ++ng;
        } else {
            UIRectF b; b.l=tmp[best].l; b.t=tmp[best].t; b.r=tmp[best].r; b.b=tmp[best].b;
            rect_union(&b,&r); tmp[best].l=b.l; tmp[best].t=b.t; tmp[best].r=b.r; tmp[best].b=b.b;
            if(!tmp[best].stable_id && hint) tmp[best].stable_id=hint;
        }
    }

    /* Transitive merge: A can touch B after either expanded. */
    for(pass=0; pass<MAX_UI_GROUPS; ++pass) {
        int changed=0;
        for(i=0;i<ng && !changed;++i) for(j=i+1;j<ng;++j) {
            UIRectF a,b;
            if(tmp[i].is_global != tmp[j].is_global) continue;
            if(tmp[i].stable_id && tmp[j].stable_id && tmp[i].stable_id!=tmp[j].stable_id) continue;
            a.l=tmp[i].l;a.t=tmp[i].t;a.r=tmp[i].r;a.b=tmp[i].b;
            b.l=tmp[j].l;b.t=tmp[j].t;b.r=tmp[j].r;b.b=tmp[j].b;
            if(rect_near(&a,&b,gap)) {
                rect_union(&a,&b);
                tmp[i].l=a.l;tmp[i].t=a.t;tmp[i].r=a.r;tmp[i].b=a.b;
                if(!tmp[i].stable_id) tmp[i].stable_id=tmp[j].stable_id;
                tmp[j]=tmp[ng-1]; --ng; changed=1; break;
            }
        }
        if(!changed) break;
    }
    /* Match each freshly clustered group to one previous full-frame group.
       A matched group keeps the exact same anchor/stable id while it moves,
       so dragging cannot cross an anchor threshold and snap. */
    {
        BYTE used_prev[MAX_UI_GROUPS];
        for(i=0;i<MAX_UI_GROUPS;++i) used_prev[i]=0;
        for(i=0;i<ng;++i) {
            UIRectF nb; int best=-1; float best_score=999999999.0f;
            float ncx,ncy,nw,nh;
            nb.l=tmp[i].l;nb.t=tmp[i].t;nb.r=tmp[i].r;nb.b=tmp[i].b;
            ncx=(nb.l+nb.r)*0.5f; ncy=(nb.t+nb.b)*0.5f; nw=nb.r-nb.l; nh=nb.b-nb.t;
            if(tmp[i].stable_id) {
                for(j=0;j<g_ui_prev_group_count;++j) {
                    if(!used_prev[j] && g_ui_prev_groups[j].stable_id==tmp[i].stable_id) { best=(int)j; break; }
                }
            }
            if(best<0) for(j=0;j<g_ui_prev_group_count;++j) {
                UIRectF ob; float ocx,ocy,ow,oh,dx,dy,dw,dh,score;
                if(used_prev[j]) continue;
                if(g_ui_prev_groups[j].is_global != tmp[i].is_global) continue;
                ob.l=g_ui_prev_groups[j].l;ob.t=g_ui_prev_groups[j].t;ob.r=g_ui_prev_groups[j].r;ob.b=g_ui_prev_groups[j].b;
                if(!rect_near(&nb,&ob,(float)g_ui_stable_match_gap)) continue;
                ocx=(ob.l+ob.r)*0.5f; ocy=(ob.t+ob.b)*0.5f; ow=ob.r-ob.l; oh=ob.b-ob.t;
                dx=f_abs(ncx-ocx); dy=f_abs(ncy-ocy); dw=f_abs(nw-ow); dh=f_abs(nh-oh);
                score=dx+dy+(dw+dh)*0.35f;
                if(score<best_score) { best=(int)j; best_score=score; }
            }
            if(best>=0) {
                used_prev[best]=1;
                tmp[i].ax=g_ui_prev_groups[best].ax;
                tmp[i].ay=g_ui_prev_groups[best].ay;
                tmp[i].stable_id=g_ui_prev_groups[best].stable_id;
            } else {
                choose_group_anchor(&nb,&tmp[i].ax,&tmp[i].ay);
                tmp[i].stable_id=g_ui_next_stable_id++;
                if(g_ui_next_stable_id==0) g_ui_next_stable_id=1;
            }
        }
    }

    /* Keep real member rectangles for hit gating. The inverse mouse transform
       is group-based, not primitive-based. */
    for(i=0;i<g_ui_frame_rect_count && nm<MAX_UI_FRAME_RECTS;++i) {
        UIRectF r=g_ui_frame_rects[i]; int best=-1; float best_area=999999999.0f;
        if(rect_is_global(&r) && !g_ui_scale_global) continue;
        for(j=0;j<ng;++j) {
            UIRectF b; float area;
            b.l=tmp[j].l;b.t=tmp[j].t;b.r=tmp[j].r;b.b=tmp[j].b;
            if(!rect_near(&r,&b,0.5f)) continue;
            area=rect_area(&b);
            if(area<best_area) { best=(int)j; best_area=area; }
        }
        if(best>=0) { members[nm].rect=r; members[nm].group_index=(WORD)best; ++nm; }
    }

    ui_group_lock();
    g_ui_prev_group_count=ng;
    for(i=0;i<ng;++i) g_ui_prev_groups[i]=tmp[i];
    g_ui_prev_member_count=nm;
    for(i=0;i<nm;++i) g_ui_prev_members[i]=members[i];
    ++g_ui_group_generation;
    ui_group_unlock();
}

/* The settings window publishes requests; only the render boundary applies
 * them. Defer changes until a native drag/control capture has ended. */
static int g_settings_request_valid,g_settings_request_scale,g_settings_request_enabled;
static int g_settings_request_crisp,g_settings_request_keep,g_settings_request_save;
static void ui_settings_apply(int percent,int enabled,int crisp,int keep,int save) {
    if(percent<100 || percent>200) return;
    g_settings_request_scale=percent; g_settings_request_enabled=enabled!=0;
    g_settings_request_crisp=crisp!=0; g_settings_request_keep=keep!=0;
    g_settings_request_save=save!=0; g_settings_request_valid=1;
}
static void ui_settings_commit(void) {
    char line[160];
    if(!g_settings_request_valid || owner_native_capture()) return;
    g_settings_request_valid=0;
    g_ui_scale_percent=g_settings_request_scale;
    g_ui_enabled=1; g_ui_runtime_enabled=g_settings_request_enabled;
    g_ui_sharp_filter=g_settings_request_crisp; g_ui_keep_on_screen=g_settings_request_keep;
    line[0]=0; s_append(line,sizeof(line),"Settings applied: scale=");
    s_append_uint(line,sizeof(line),(DWORD)g_ui_scale_percent);
    s_append(line,sizeof(line)," enabled="); s_append_uint(line,sizeof(line),(DWORD)g_ui_runtime_enabled);
    s_append(line,sizeof(line)," crisp="); s_append_uint(line,sizeof(line),(DWORD)g_ui_sharp_filter);
    s_append(line,sizeof(line)," keepOnScreen="); s_append_uint(line,sizeof(line),(DWORD)g_ui_keep_on_screen);
    log_line(line);
    if(g_settings_request_save) {
        typedef BOOL (WINAPI *PFN_SaveIni)(LPCSTR,LPCSTR,LPCSTR,LPCSTR);
        HMODULE k32=find_loaded_module("kernel32.dll");
        PFN_SaveIni write=(PFN_SaveIni)resolve_export(k32,"WritePrivateProfileStringA");
        char percent[16]; int ok=write!=0;
        percent[0]=0; s_append_uint(percent,sizeof(percent),(DWORD)g_ui_scale_percent);
        if(write) {
            if(!write("UI","ScalePercent",percent,g_ini_path)) ok=0;
            if(!write("UI","Enabled",g_ui_runtime_enabled?"1":"0",g_ini_path)) ok=0;
            if(!write("UI","SharpFilter",g_ui_sharp_filter?"1":"0",g_ini_path)) ok=0;
            if(!write("UI","KeepOnScreen",g_ui_keep_on_screen?"1":"0",g_ini_path)) ok=0;
        }
        log_line(ok?"Settings saved to prm-ui-fix.ini":"Settings save failed; live settings remain applied");
    }
}
static void ui_settings_poll(void);
static void ui_settings_publish_snapshot(void);

static void ui_present_boundary(const char* method) {
    char line[224]; DWORD rects=g_ui_frame_rect_count, owner_rects=g_owner_frame_member_count, submits=g_owner_submit_count;
    g_ui_present_seen=1;
    ++g_ui_present_serial;
    if(g_GetTickCount) g_ui_last_present_tick=g_GetTickCount();
    owner_finalize_frame();
    finalize_ui_frame();
    owner_submit_finish_present();
    clear_ui_frame_accumulator();
    g_ui_scenes_since_present=0;
    owner_install_active_vtables();
    vtrace_install_active_vtables();
    vtrace_maybe_finish();
    ui_settings_poll();
    ui_settings_commit();
    ui_settings_publish_snapshot();
    if(g_ui_present_serial<=6) {
        line[0]=0; s_append(line,sizeof(line),"UI present #"); s_append_uint(line,sizeof(line),g_ui_present_serial);
        s_append(line,sizeof(line)," via "); s_append(line,sizeof(line),method);
        s_append(line,sizeof(line)," geomRects="); s_append_uint(line,sizeof(line),rects);
        s_append(line,sizeof(line)," ownerRects="); s_append_uint(line,sizeof(line),owner_rects);
        s_append(line,sizeof(line)," submits="); s_append_uint(line,sizeof(line),submits);
        s_append(line,sizeof(line)," matched="); s_append_uint(line,sizeof(line),g_owner_submit_last_matched);
        s_append(line,sizeof(line)," groups="); s_append_uint(line,sizeof(line),g_ui_prev_group_count);
        log_line(line);
    }
    if(g_owner_submit_enabled && g_ui_present_serial>0 && (g_ui_present_serial%1200UL)==0) {
        line[0]=0; s_append(line,sizeof(line),"3B heartbeat present="); s_append_uint(line,sizeof(line),g_ui_present_serial);
        s_append(line,sizeof(line)," matched="); s_append_uint(line,sizeof(line),g_owner_submit_total_matched);
        s_append(line,sizeof(line)," tagged="); s_append_uint(line,sizeof(line),g_owner_tagged_draws);
        s_append(line,sizeof(line)," pending="); s_append_uint(line,sizeof(line),g_owner_submit_count);
        s_append(line,sizeof(line)," overflow="); s_append_uint(line,sizeof(line),g_owner_submit_total_overflow);
        s_append(line,sizeof(line)," posInvalid="); s_append_uint(line,sizeof(line),g_owner_submit_pos_invalid);
        s_append(line,sizeof(line)," ownerRegions="); s_append_uint(line,sizeof(line),g_owner_input_region_count);
        s_append(line,sizeof(line)," managerRegions="); s_append_uint(line,sizeof(line),g_owner_input_manager_regions);
        s_append(line,sizeof(line)," graceRegions="); s_append_uint(line,sizeof(line),g_owner_input_grace_regions);
        s_append(line,sizeof(line)," ownerMouse="); s_append_uint(line,sizeof(line),g_owner_mapped_mouse);
        s_append(line,sizeof(line)," ownerCandidates="); s_append_uint(line,sizeof(line),g_owner_input_candidates);
        s_append(line,sizeof(line)," ownerOverlaps="); s_append_uint(line,sizeof(line),g_owner_input_overlap_hits);
        s_append(line,sizeof(line)," fallbackMouse="); s_append_uint(line,sizeof(line),g_ui_mapped_mouse); log_line(line);
    }
}

static int surface_dimensions(void* surf, DWORD* w, DWORD* h) {
    BYTE desc[124]; unsigned int i; void** vt; PFN_DDS7_GetSurfaceDesc fn;
    if(w)*w=0;if(h)*h=0;if(!surf)return 0;
    for(i=0;i<sizeof(desc);++i) desc[i]=0; *(DWORD*)(desc+0)=124;
    vt=*(void***)surf;if(!vt)return 0; fn=(PFN_DDS7_GetSurfaceDesc)vt[22];
    if(!fn || fn(surf,desc)<0)return 0;
    if(h)*h=*(DWORD*)(desc+8);if(w)*w=*(DWORD*)(desc+12);return 1;
}

static int surface_is_screenish(void* surf) {
    DWORD w=0,h=0; if(!surface_dimensions(surf,&w,&h))return 0;
    return w>=(DWORD)(g_ui_screen_w*3/4) && h>=(DWORD)(g_ui_screen_h*3/4);
}

static int blt_is_present(void* self, const RECT* dst, void* src, const RECT* srcRect) {
    LONG dw,dh,sw,sh;
    if(!src || !(g_ui_frame_rect_count || g_owner_frame_member_count || g_owner_submit_count || g_owner_bitmap_frame_calls)) return 0;
    if(is_render_target(src) && surface_is_screenish(self)) return 1;
    if(is_render_target(self) && surface_is_screenish(src)) return 1;
    if(!surface_is_screenish(self) || !surface_is_screenish(src)) return 0;
    dw = dst ? (dst->right-dst->left) : g_ui_screen_w;
    dh = dst ? (dst->bottom-dst->top) : g_ui_screen_h;
    sw = srcRect ? (srcRect->right-srcRect->left) : g_ui_screen_w;
    sh = srcRect ? (srcRect->bottom-srcRect->top) : g_ui_screen_h;
    return dw>g_ui_screen_w/2 && dh>g_ui_screen_h/2 && sw>g_ui_screen_w/2 && sh>g_ui_screen_h/2;
}

/* Deep tracing established this discriminator for the classic 2D UI family. */
static int looks_like_ui_vertices(DWORD prim, DWORD fvf, const void* verts, DWORD nverts) {
    DWORD stride, i; const BYTE* p=(const BYTE*)verts;
    if(!g_ui_enabled || !g_ui_runtime_enabled || !p) return 0;
    if(fvf != 0x000001C4UL) return 0;
    if(!(prim==4 || prim==5)) return 0;
    if(nverts < 3 || nverts > 16) return 0;
    stride=fvf_stride(fvf); if(stride < 16 || stride > 64) return 0;
    for(i=0;i<nverts;++i) {
        const float* v=(const float*)(p+i*stride);
        float x=v[0], y=v[1], z=v[2], rhw=v[3];
        if(f_abs(z) > 0.010f) return 0;
        if(rhw < 0.90f || rhw > 1.10f) return 0;
        if(x < -128.0f || x > (float)g_ui_screen_w + 128.0f) return 0;
        if(y < -128.0f || y > (float)g_ui_screen_h + 128.0f) return 0;
    }
    return 1;
}

static const void* make_scaled_ui_vertices(DWORD prim, DWORD fvf, const void* verts, DWORD nverts, BYTE* scratch, DWORD scratch_cap, void* frame, DWORD caller_rva) {
    DWORD stride, bytes, i, j;
    float minx=999999.0f,miny=999999.0f,maxx=-999999.0f,maxy=-999999.0f,ax,ay,s=ui_scale_factor(),dx=0.0f,dy=0.0f;
    UIRectF r; int bitmap_owned;
    /* These exact native calls assemble child pixels into an offscreen window
       cache. Scaling them would distort the cache before its final screen draw. */
    if(caller_rva==PRM_OFFSCREEN_DP_RETURN_RVA || caller_rva==PRM_OFFSCREEN_DIP_RETURN_RVA) {
        ++g_owner_bitmap_offscreen; return verts;
    }
    if(cursor_consume_vertices(fvf,verts,nverts)) return verts;
    bitmap_owned=owner_bitmap_consume_transform(fvf,verts,nverts,&ax,&ay,&s,&dx,&dy);
    if(bitmap_owned==2) return verts;
    if(bitmap_owned) {
        /* Exact native provenance remains valid at the screen edge. Applying
           the fallback XY bounds per tile would split a partly offscreen window. */
        if(!g_ui_enabled || !g_ui_runtime_enabled) return verts;
    } else if(!looks_like_ui_vertices(prim,fvf,verts,nverts)) return verts;
    vtrace_note_d3d_ui();
    stride=fvf_stride(fvf); bytes=stride*nverts; if(bytes>scratch_cap) return verts;
    for(i=0;i<nverts;++i) {
        const float* v=(const float*)((const BYTE*)verts+i*stride);
        if(v[0]<minx)minx=v[0];if(v[0]>maxx)maxx=v[0];
        if(v[1]<miny)miny=v[1];if(v[1]>maxy)maxy=v[1];
    }
    r.l=minx;r.t=miny;r.r=maxx;r.b=maxy;
    if(bitmap_owned) {
        ++g_owner_tagged_draws;
    } else {
        DWORD submit_owner=0;
        if(!g_owner_bitmap_hooks_installed && g_owner_submit_enabled && owner_submit_match_rect(&r,&submit_owner) && owner_state_for(submit_owner,1)) {
            owner_collect_rect(submit_owner,&r);
            ++g_owner_tagged_draws;
            /* First frame learns the real window bbox/anchor and is allowed to
               remain native-sized. From the next present onward this object has
               its own stable transform, independent of neighboring windows. */
            if(!owner_get_transform(submit_owner,&ax,&ay)) return verts;
        } else {
            collect_ui_rect(minx,miny,maxx,maxy);
            if(rect_is_global(&r) && !g_ui_scale_global) return verts;
            if(!get_group_transform_for_rect(&r,&ax,&ay)) {
                if(!g_ui_scale_unmatched) return verts;
                choose_group_anchor(&r,&ax,&ay);
            }
        }
    }
    for(j=0;j<bytes;++j) scratch[j]=((const BYTE*)verts)[j];
    for(i=0;i<nverts;++i) {
        float* v=(float*)(scratch+i*stride);
        v[0]=ax+(v[0]-ax)*s+dx; v[1]=ay+(v[1]-ay)*s+dy;
    }
    ++g_ui_scaled_draws;
    return scratch;
}

static void maybe_toggle_ui_sharp(void) {
    short k; if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_UI_SHARP);
    if(k&1) { g_ui_sharp_filter=!g_ui_sharp_filter; log_line(g_ui_sharp_filter?"UI filtering: CRISP (F3)":"UI filtering: NATIVE (F3)"); }
}
static void maybe_toggle_ui_scale(void) {
    short k; if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_UI_SCALE);
    if(k&1) { g_ui_runtime_enabled=!g_ui_runtime_enabled; log_line(g_ui_runtime_enabled?"UI scaling: ON (F5)":"UI scaling: OFF (F5)"); }
}
static void maybe_toggle_ui_input(void) {
    short k; if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_UI_INPUT);
    if(k&1) { g_input_runtime_enabled=!g_input_runtime_enabled; log_line(g_input_runtime_enabled?"UI mouse remap (full owner + 2F fallback): ON (F6)":"UI mouse remap (full owner + 2F fallback): OFF (F6)"); }
}
static void maybe_toggle_world_input(void) {
    short k; if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_WORLD_INPUT);
    if(k&1) { g_world_input_enabled=!g_world_input_enabled; log_line(g_world_input_enabled?"World click correction: ON (F9)":"World click correction: OFF (F9)"); }
}
static void maybe_dump_ui_groups(void) {
    short k; DWORD i,n; char line[256];
    if(!g_GetAsyncKeyState) return; k=g_GetAsyncKeyState(VK_UI_GROUP_DUMP); if(!(k&1)) return;
    ui_group_lock(); n=g_ui_prev_group_count;
    line[0]=0;s_append(line,sizeof(line),"UI groups present=");s_append_uint(line,sizeof(line),g_ui_present_serial);s_append(line,sizeof(line)," generation=");s_append_uint(line,sizeof(line),g_ui_group_generation);s_append(line,sizeof(line)," count=");s_append_uint(line,sizeof(line),n);log_line(line);
    for(i=0;i<n && i<24;++i) {
        UIGroup* g=&g_ui_prev_groups[i]; UIRectF src,dst;
        src.l=g->l;src.t=g->t;src.r=g->r;src.b=g->b; transform_bounds(&src,g->ax,g->ay,&dst);
        line[0]=0;s_append(line,sizeof(line)," group#");s_append_uint(line,sizeof(line),i);s_append(line,sizeof(line)," id=");s_append_uint(line,sizeof(line),g->stable_id);
        s_append(line,sizeof(line)," src=");s_append_uint(line,sizeof(line),(DWORD)(src.l<0?0:src.l));s_append(line,sizeof(line),",");s_append_uint(line,sizeof(line),(DWORD)(src.t<0?0:src.t));s_append(line,sizeof(line),"..");s_append_uint(line,sizeof(line),(DWORD)(src.r<0?0:src.r));s_append(line,sizeof(line),",");s_append_uint(line,sizeof(line),(DWORD)(src.b<0?0:src.b));
        s_append(line,sizeof(line)," anchor=");s_append_uint(line,sizeof(line),(DWORD)g->ax);s_append(line,sizeof(line),",");s_append_uint(line,sizeof(line),(DWORD)g->ay);
        s_append(line,sizeof(line)," dst=");s_append_uint(line,sizeof(line),(DWORD)(dst.l<0?0:dst.l));s_append(line,sizeof(line),",");s_append_uint(line,sizeof(line),(DWORD)(dst.t<0?0:dst.t));s_append(line,sizeof(line),"..");s_append_uint(line,sizeof(line),(DWORD)(dst.r<0?0:dst.r));s_append(line,sizeof(line),",");s_append_uint(line,sizeof(line),(DWORD)(dst.b<0?0:dst.b));
        log_line(line);
    }
    ui_group_unlock();
}

/* Gate on a real member rectangle, then invert the owning group's ONE shared
   transform. This is the key difference from Phase 2D's per-quad remap. */
static int remap_ui_point(POINT* p) {
    DWORD i; int found=-1; float best_area=999999999.0f, px,py;
    UIGroup group;
    if(!p || !g_input_enabled || !g_input_runtime_enabled || !g_ui_runtime_enabled) return 0;
    px=(float)p->x;py=(float)p->y;
    ui_group_lock();
    for(i=0;i<g_ui_prev_member_count;++i) {
        UIGroupMember* m=&g_ui_prev_members[i]; UIGroup* g; UIRectF dst; float area;
        if(m->group_index>=g_ui_prev_group_count) continue;
        g=&g_ui_prev_groups[m->group_index]; transform_bounds(&m->rect,g->ax,g->ay,&dst);
        if(!rect_contains_point(&dst,px,py)) continue;
        area=rect_area(&dst);
        if(area<best_area) { found=(int)m->group_index; best_area=area; }
    }
    if(found>=0) group=g_ui_prev_groups[found];
    ui_group_unlock();
    if(found>=0) {
        float s=ui_scale_factor(); float x,y;
        if(s<0.01f) return 0;
        x=group.ax+(px-group.ax)/s; y=group.ay+(py-group.ay)/s;
        p->x=(LONG)(x>=0.0f?x+0.5f:x-0.5f);
        p->y=(LONG)(y>=0.0f?y+0.5f:y-0.5f);
        ++g_ui_mapped_mouse; return 1;
    }
    return 0;
}

static BOOL WINAPI hook_ScreenToClient(HWND hwnd, POINT* p) {
    BOOL ok; DWORD caller_rva=ptr_to_rva(__builtin_return_address(0));
    OwnerHitSelection hit={0}; int primary=caller_rva==PRM_UI_MOUSE_RETURN_RVA;
    maybe_toggle_ui_input(); maybe_toggle_world_input(); maybe_dump_ui_groups(); maybe_dump_owner_windows(); vtrace_poll_hotkey();
    if(primary) owner_hit_publish(&hit);
    if(!g_real_ScreenToClient) return FALSE;
    ok=g_real_ScreenToClient(hwnd,p);
    if(ok) {
        POINT raw=*p;
        if(primary) g_input_hwnd=hwnd;
        if(g_owner_input_remap_enabled) {
            if(!remap_owner_point_selected(p,primary?&hit:0)) remap_ui_point(p);
        } else remap_ui_point(p);
        if(primary) {
            if(!hit.valid && g_owner_input_remap_enabled && g_owner_scale_enabled &&
               g_input_enabled && g_input_runtime_enabled && g_ui_runtime_enabled &&
               g_GetCurrentThreadId && !owner_native_capture()) {
                hit.raw=raw; hit.mapped=*p; hit.thread=g_GetCurrentThreadId();
                hit.valid=hit.thread!=0;
            }
            owner_hit_publish(&hit);
        }
    }
    return ok;
}

static void install_input_hooks(void) {
    HMODULE exe=g_GetModuleHandleA?g_GetModuleHandleA(0):0;
    HMODULE u32=find_loaded_module("user32.dll"); int a=0;
    if(u32) {
        g_GetCursorPos=(PFN_GetCursorPos)resolve_export(u32,"GetCursorPos");
        g_GetClientRect=(PFN_GetClientRect)resolve_export(u32,"GetClientRect");
    }
    log_line(g_GetCursorPos && g_GetClientRect?"Raw client input APIs: OK":"Raw client input APIs: missing");
    if(!exe){log_line("UI input hooks: main module not found");return;}
    a=patch_import(exe,"USER32.dll","ScreenToClient",(void*)hook_ScreenToClient,(void**)&g_real_ScreenToClient);
    log_line(a?"ScreenToClient IAT hook: OK":"ScreenToClient IAT hook: NOT FOUND");
}

static HRESULT WINAPI hook_DD7_QueryInterface(void* self, const GUID* iid, void** out) {
    DD7HookRec* r=dd7_rec(self); PFN_COM_QueryInterface fn=r?(PFN_COM_QueryInterface)r->orig_qi:0; HRESULT hr;
    static const BYTE tail[8]={0xa4,0x07,0x00,0xa0,0xc9,0x06,0x29,0xa8};
    if(!fn) return (HRESULT)0x80004005UL;
    hr=fn(self,iid,out);
    if(hr>=0 && out && *out && guid_eq(iid,0xf5049e77UL,0x4861,0x11d2,tail)) { log_line("IDirect3D7 acquired"); install_d3d7_hooks(*out); }
    return hr;
}

static HRESULT WINAPI hook_D3D7_CreateDevice(void* self, const GUID* clsid, void* target, void** out) {
    D3D7HookRec* r=d3d7_rec(self); PFN_D3D7_CreateDevice fn=r?(PFN_D3D7_CreateDevice)r->orig_create_device:0; HRESULT hr;
    if(!fn) return (HRESULT)0x80004005UL;
    hr=fn(self,clsid,target,out);
    if(hr>=0 && out && *out) {
        log_line("IDirect3DDevice7 acquired");
        remember_render_target(target);
        install_surface_hooks(target);
        install_device_hooks(*out);
    }
    return hr;
}

static HRESULT WINAPI hook_BeginScene(void* self) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_BeginScene fn=r?(PFN_D3D7_BeginScene)r->orig_begin_scene:0;
    ++g_ui_scene_serial; ++g_ui_scenes_since_present;
    return fn ? fn(self) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_EndScene(void* self) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_EndScene fn=r?(PFN_D3D7_EndScene)r->orig_end_scene:0;
    /* Safety fallback only if no actual DirectDraw presentation has ever been
       observed. Accumulate several scenes instead of treating every pass as a
       frame (the Phase 2E bug). */
    if(!g_ui_present_seen && g_ui_scenes_since_present>=4 && (g_ui_frame_rect_count || g_owner_frame_member_count || g_owner_bitmap_frame_calls)) {
        if(!g_ui_fallback_logged) { log_line("Present hook not yet observed: using 4-scene grouping fallback"); g_ui_fallback_logged=1; }
        ++g_ui_present_serial; owner_finalize_frame(); finalize_ui_frame(); clear_ui_frame_accumulator(); owner_install_active_vtables(); g_ui_scenes_since_present=0;
    }
    return fn ? fn(self) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_SurfaceFlip(void* self, void* targetOverride, DWORD flags) {
    SurfHookRec* r=surf_rec(self); PFN_DDS7_Flip fn=r?(PFN_DDS7_Flip)r->orig_flip:0;
    if(g_ui_frame_rect_count || g_owner_frame_member_count || g_owner_bitmap_frame_calls) ui_present_boundary("Flip");
    return fn ? fn(self,targetOverride,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_SurfaceBlt(void* self, RECT* dst, void* src, RECT* srcRect, DWORD flags, void* fx) {
    SurfHookRec* r=surf_rec(self); PFN_DDS7_Blt fn=r?(PFN_DDS7_Blt)r->orig_blt:0;
    if(blt_is_present(self,dst,src,srcRect)) ui_present_boundary("Blt");
    return fn ? fn(self,dst,src,srcRect,flags,fx) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_SurfaceBltFast(void* self, DWORD x, DWORD y, void* src, RECT* srcRect, DWORD flags) {
    SurfHookRec* r=surf_rec(self); PFN_DDS7_BltFast fn=r?(PFN_DDS7_BltFast)r->orig_bltfast:0;
    (void)x;(void)y;
    if((g_ui_frame_rect_count || g_owner_frame_member_count || g_owner_bitmap_frame_calls) && src && surface_is_screenish(self) && surface_is_screenish(src)) ui_present_boundary("BltFast");
    return fn ? fn(self,x,y,src,srcRect,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_SetTexture(void* self, DWORD stage, void* tex) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_SetTexture fn=r?(PFN_D3D7_SetTexture)r->orig_set_texture:0;
    if(stage==0) { g_current_texture=tex; capture_texture_desc(tex); }
    return fn ? fn(self,stage,tex) : (HRESULT)0x80004005UL;
}

/* Native UI textures use LINEAR min/mag filtering. Override only a draw whose
 * screen vertices we actually scaled; cursor, world, native-size labels and
 * offscreen composition keep their original states. Read the actual device
 * state (including state-block changes), and restore it before returning. */
typedef struct {
    PFN_D3D7_SetTextureStageState set;
    DWORD mag,min,changed;
} UIFilterScope;
static void ui_filter_end(void* self, UIFilterScope* scope) {
    if(!scope->set) return;
    if((scope->changed&1) && scope->set(self,0,16,scope->mag)<0) ++g_ui_sharp_failures;
    if((scope->changed&2) && scope->set(self,0,17,scope->min)<0) ++g_ui_sharp_failures;
    scope->changed=0;
}
static void ui_filter_begin(void* self, int scaled, UIFilterScope* scope) {
    void** vt; PFN_D3D7_GetTextureStageState get;
    scope->set=0; scope->changed=0;
    if(!g_ui_sharp_filter || !scaled || !self) return;
    vt=*(void***)self; if(!vt || !vt[36] || !vt[37]) return;
    get=(PFN_D3D7_GetTextureStageState)vt[36];
    if(get(self,0,16,&scope->mag)<0 || get(self,0,17,&scope->min)<0) {
        ++g_ui_sharp_failures; return;
    }
    scope->set=(PFN_D3D7_SetTextureStageState)vt[37];
    if(scope->mag!=1) {
        scope->changed|=1;
        if(scope->set(self,0,16,1)<0) { ++g_ui_sharp_failures; ui_filter_end(self,scope); return; }
    }
    if(scope->min!=1) {
        scope->changed|=2;
        if(scope->set(self,0,17,1)<0) { ++g_ui_sharp_failures; ui_filter_end(self,scope); return; }
    }
    ++g_ui_sharp_draws;
}

static HRESULT WINAPI hook_DrawPrimitive(void* self, DWORD prim, DWORD fvf, const void* verts, DWORD nverts, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawPrimitive fn=r?(PFN_D3D7_DrawPrimitive)r->orig_draw:0; void* caller=__builtin_return_address(0);
    BYTE scratch[1024]; const void* out_verts; UIFilterScope filter; HRESULT hr;
    maybe_toggle_ui_sharp();
    maybe_toggle_ui_scale();
    maybe_toggle_ui_input();
    maybe_dump_ui_groups();
    maybe_dump_owner_windows();
    vtrace_poll_hotkey();
    maybe_start_capture(); add_draw_stat(0,prim,fvf,nverts,verts,caller,__builtin_frame_address(0)); maybe_finish_capture();
    out_verts=make_scaled_ui_vertices(prim,fvf,verts,nverts,scratch,sizeof(scratch),__builtin_frame_address(0),ptr_to_rva(caller));
    if(!fn) return (HRESULT)0x80004005UL;
    ui_filter_begin(self,out_verts!=verts,&filter);
    hr=fn(self,prim,fvf,out_verts,nverts,flags);
    ui_filter_end(self,&filter);
    return hr;
}

static HRESULT WINAPI hook_DrawIndexedPrimitive(void* self, DWORD prim, DWORD fvf, const void* verts, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawIndexedPrimitive fn=r?(PFN_D3D7_DrawIndexedPrimitive)r->orig_draw_indexed:0; void* caller=__builtin_return_address(0);
    BYTE scratch[1024]; const void* out_verts; UIFilterScope filter; HRESULT hr;
    maybe_toggle_ui_sharp();
    maybe_toggle_ui_scale();
    maybe_toggle_ui_input();
    maybe_dump_ui_groups();
    maybe_dump_owner_windows();
    vtrace_poll_hotkey();
    maybe_start_capture(); add_draw_stat(1,prim,fvf,nverts,verts,caller,__builtin_frame_address(0)); maybe_finish_capture();
    out_verts=make_scaled_ui_vertices(prim,fvf,verts,nverts,scratch,sizeof(scratch),__builtin_frame_address(0),ptr_to_rva(caller));
    if(!fn) return (HRESULT)0x80004005UL;
    ui_filter_begin(self,out_verts!=verts,&filter);
    hr=fn(self,prim,fvf,out_verts,nverts,idx,nidx,flags);
    ui_filter_end(self,&filter);
    return hr;
}

static HRESULT WINAPI hook_DrawPrimitiveStrided(void* self, DWORD prim, DWORD fvf, const void* data, DWORD nverts, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawPrimitiveStrided fn=r?(PFN_D3D7_DrawPrimitiveStrided)r->orig_draw_strided:0; void* caller=__builtin_return_address(0);
    maybe_start_capture(); add_draw_stat(2,prim,fvf,nverts,0,caller,__builtin_frame_address(0)); maybe_finish_capture();
    return fn ? fn(self,prim,fvf,data,nverts,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_DrawIndexedPrimitiveStrided(void* self, DWORD prim, DWORD fvf, const void* data, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawIndexedPrimitiveStrided fn=r?(PFN_D3D7_DrawIndexedPrimitiveStrided)r->orig_draw_indexed_strided:0; void* caller=__builtin_return_address(0);
    maybe_start_capture(); add_draw_stat(3,prim,fvf,nverts,0,caller,__builtin_frame_address(0)); maybe_finish_capture();
    return fn ? fn(self,prim,fvf,data,nverts,idx,nidx,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_DrawPrimitiveVB(void* self, DWORD prim, void* vb, DWORD start, DWORD nverts, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawPrimitiveVB fn=r?(PFN_D3D7_DrawPrimitiveVB)r->orig_draw_vb:0; void* caller=__builtin_return_address(0);
    maybe_start_capture(); add_draw_stat(4,prim,0,nverts,0,caller,__builtin_frame_address(0)); maybe_finish_capture();
    return fn ? fn(self,prim,vb,start,nverts,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_DrawIndexedPrimitiveVB(void* self, DWORD prim, void* vb, DWORD start, DWORD nverts, const WORD* idx, DWORD nidx, DWORD flags) {
    DevHookRec* r=dev_rec(self); PFN_D3D7_DrawIndexedPrimitiveVB fn=r?(PFN_D3D7_DrawIndexedPrimitiveVB)r->orig_draw_indexed_vb:0; void* caller=__builtin_return_address(0);
    maybe_start_capture(); add_draw_stat(5,prim,0,nverts,0,caller,__builtin_frame_address(0)); maybe_finish_capture();
    return fn ? fn(self,prim,vb,start,nverts,idx,nidx,flags) : (HRESULT)0x80004005UL;
}

static HRESULT WINAPI hook_DirectDrawCreateEx(void* guid, void** out, const GUID* iid, void* outer) {
    HRESULT hr;
    if(!g_real_DirectDrawCreateEx) return (HRESULT)0x80004005UL;
    hr=g_real_DirectDrawCreateEx(guid,out,iid,outer);
    if(hr>=0 && out && *out) { log_line("DirectDrawCreateEx: IDirectDraw7 acquired"); install_dd7_hooks(*out); }
    return hr;
}

static void install_phase2_hooks(void) {
    int ok=0;
    if(!g_exe) return;
    ok=patch_import(g_exe,"DDRAW.dll","DirectDrawCreateEx",(void*)hook_DirectDrawCreateEx,(void**)&g_real_DirectDrawCreateEx);
    log_line(ok ? "DirectDrawCreateEx IAT hook: OK" : "DirectDrawCreateEx IAT hook: NOT FOUND");
    if(ok) log_line("Phase 3B renderer armed: all-window owner UI + isolated world input");
}

/* ---------- real WINMM ---------- */
static void ensure_real_winmm(void) {
    char sys[520];
    if (g_real_winmm) return;
    if (!g_LoadLibraryA || !g_GetSystemDirectoryA) return;
    sys[0] = 0;
    if (!g_GetSystemDirectoryA(sys, sizeof(sys))) return;
    s_append(sys, sizeof(sys), "\\winmm.dll");
    g_real_winmm = g_LoadLibraryA(sys);
    if (!g_real_winmm || g_real_winmm == g_self) { g_real_winmm = 0; return; }
    g_real_timeBeginPeriod = (PFN_timeBeginPeriod)resolve_export(g_real_winmm, "timeBeginPeriod");
    g_real_timeEndPeriod   = (PFN_timeEndPeriod)resolve_export(g_real_winmm, "timeEndPeriod");
    g_real_timeGetDevCaps  = (PFN_timeGetDevCaps)resolve_export(g_real_winmm, "timeGetDevCaps");
    g_real_timeGetTime     = (PFN_timeGetTime)resolve_export(g_real_winmm, "timeGetTime");
}

/* Called by naked forwarding stubs for WINMM exports other than the four PRM uses directly. */
void* WINAPI resolve_winmm_name(const char* name) {
    if (!g_LoadLibraryA) bootstrap_kernel32();
    ensure_real_winmm();
    if (!g_real_winmm) return 0;
    return resolve_export(g_real_winmm, name);
}

#include "ui_settings.h"

static void initialize_mod(void) {
    HMODULE exe;
    DWORD ts = 0, image = 0, text_hash = 0;
    bootstrap_kernel32();
    init_paths();
    log_line("=== PRM UI FIX Phase 3B Owned UI Screen Bounds ===");
    log_line("Proxy DLL loaded");
    if (g_GetPrivateProfileIntA) {
        g_font_enabled = (int)g_GetPrivateProfileIntA("Font", "Enabled", 1, g_ini_path);
        g_font_add = (int)g_GetPrivateProfileIntA("Font", "AddSize", 0, g_ini_path);
        if (g_font_add < 0) g_font_add = 0;
        if (g_font_add > 12) g_font_add = 12;
        g_trace_enabled = (int)g_GetPrivateProfileIntA("Trace", "Enabled", 0, g_ini_path);
        g_trace_capture_ms = (DWORD)g_GetPrivateProfileIntA("Trace", "CaptureMs", 2000, g_ini_path);
        g_ui_enabled = (int)g_GetPrivateProfileIntA("UI", "Enabled", 1, g_ini_path);
        g_ui_scale_percent = (int)g_GetPrivateProfileIntA("UI", "ScalePercent", 133, g_ini_path);
        g_ui_sharp_filter = g_GetPrivateProfileIntA("UI", "SharpFilter", 0, g_ini_path)!=0;
        g_ui_keep_on_screen = g_GetPrivateProfileIntA("UI", "KeepOnScreen", 1, g_ini_path)!=0;
        g_ui_origin_x = (LONG)(int)g_GetPrivateProfileIntA("UI", "OriginX", 0, g_ini_path);
        g_ui_origin_y = (LONG)(int)g_GetPrivateProfileIntA("UI", "OriginY", 0, g_ini_path);
        g_ui_screen_w = (LONG)(int)g_GetPrivateProfileIntA("UI", "ScreenWidth", 3440, g_ini_path);
        g_ui_screen_h = (LONG)(int)g_GetPrivateProfileIntA("UI", "ScreenHeight", 1440, g_ini_path);
        g_ui_anchor_mode = (int)g_GetPrivateProfileIntA("UI", "AnchorMode", 1, g_ini_path);
        g_ui_group_gap = (int)g_GetPrivateProfileIntA("UI", "GroupGap", 12, g_ini_path);
        g_ui_match_gap = (int)g_GetPrivateProfileIntA("UI", "MatchGap", 40, g_ini_path);
        g_ui_stable_match_gap = (int)g_GetPrivateProfileIntA("UI", "StableMatchGap", 96, g_ini_path);
        g_ui_global_threshold_percent = (int)g_GetPrivateProfileIntA("UI", "GlobalThresholdPercent", 65, g_ini_path);
        g_ui_scale_global = (int)g_GetPrivateProfileIntA("UI", "ScaleGlobal", 0, g_ini_path);
        g_ui_scale_unmatched = (int)g_GetPrivateProfileIntA("UI", "ScaleUnmatched", 0, g_ini_path);
        g_input_enabled = (int)g_GetPrivateProfileIntA("Input", "Enabled", 1, g_ini_path);
        g_input_max_age_ms = (DWORD)g_GetPrivateProfileIntA("Input", "HitRegionMaxAgeMs", 250, g_ini_path);
        g_world_input_enabled = (int)g_GetPrivateProfileIntA("WorldInput", "Enabled", 1, g_ini_path);
        g_world_input_normalize = (int)g_GetPrivateProfileIntA("WorldInput", "NormalizeToScreen", 1, g_ini_path);
        g_owner_submit_enabled = (int)g_GetPrivateProfileIntA("OwnerSubmit", "Enabled", 1, g_ini_path);
        g_owner_bitmap_enabled = (int)g_GetPrivateProfileIntA("OwnerBitmap", "Enabled", 1, g_ini_path);
        g_owner_tooltip_enabled = (int)g_GetPrivateProfileIntA("OwnerSubmit", "TooltipEnabled", 1, g_ini_path);
        g_owner_all_window_calls = (int)g_GetPrivateProfileIntA("OwnerSubmit", "AllWindowCalls", 1, g_ini_path);
        g_owner_submit_tolerance = (DWORD)g_GetPrivateProfileIntA("OwnerSubmit", "MatchTolerance", 4, g_ini_path);
        g_owner_submit_max_age_presents = (DWORD)g_GetPrivateProfileIntA("OwnerSubmit", "MaxAgePresents", 96, g_ini_path);
        g_owner_input_remap_enabled = (int)g_GetPrivateProfileIntA("OwnerSubmit", "OwnerInputEnabled", 1, g_ini_path);
        g_owner_input_max_age_presents = (DWORD)g_GetPrivateProfileIntA("OwnerSubmit", "OwnerInputGracePresents", 24, g_ini_path);
        g_owner_input_exact_max_age_presents = (DWORD)g_GetPrivateProfileIntA("OwnerSubmit", "OwnerInputExactAgePresents", 4, g_ini_path);
        g_owner_scale_enabled = g_owner_submit_enabled;
        g_vtrace_enabled = (int)g_GetPrivateProfileIntA("VirtualTrace", "Enabled", 0, g_ini_path);
        g_vtrace_capture_ms = (DWORD)g_GetPrivateProfileIntA("VirtualTrace", "CaptureMs", 2000, g_ini_path);
        g_vtrace_slot_first = (DWORD)g_GetPrivateProfileIntA("VirtualTrace", "SlotFirst", 0, g_ini_path);
        g_vtrace_slot_last = (DWORD)g_GetPrivateProfileIntA("VirtualTrace", "SlotLast", 39, g_ini_path);
        g_owner_render_slot = (DWORD)g_GetPrivateProfileIntA("OwnerScale", "RenderSlot", 17, g_ini_path);
        /* RenderSlot 17 is the statically validated slot for this exact PRM family. */
        if(g_owner_render_slot != 17) g_owner_render_slot = 17;
        g_owner_trace_enabled = 0;
        if (g_trace_capture_ms < 250) g_trace_capture_ms = 250;
        if (g_trace_capture_ms > 10000) g_trace_capture_ms = 10000;
        if (g_ui_scale_percent < 100) g_ui_scale_percent = 100;
        if (g_ui_scale_percent > 200) g_ui_scale_percent = 200;
        if (g_ui_screen_w < 640) g_ui_screen_w = 640;
        if (g_ui_screen_h < 480) g_ui_screen_h = 480;
        if (g_ui_anchor_mode < 0) g_ui_anchor_mode = 0;
        if (g_ui_anchor_mode > 2) g_ui_anchor_mode = 2;
        if (g_ui_group_gap < 0) g_ui_group_gap = 0;
        if (g_ui_group_gap > 128) g_ui_group_gap = 128;
        if (g_ui_match_gap < 0) g_ui_match_gap = 0;
        if (g_ui_match_gap > 256) g_ui_match_gap = 256;
        if (g_ui_stable_match_gap < 16) g_ui_stable_match_gap = 16;
        if (g_ui_stable_match_gap > 512) g_ui_stable_match_gap = 512;
        if (g_ui_global_threshold_percent < 25) g_ui_global_threshold_percent = 25;
        if (g_ui_global_threshold_percent > 95) g_ui_global_threshold_percent = 95;
        g_ui_scale_global = g_ui_scale_global ? 1 : 0;
        g_ui_scale_unmatched = g_ui_scale_unmatched ? 1 : 0;
        if (g_input_max_age_ms < 50) g_input_max_age_ms = 50;
        if (g_input_max_age_ms > 1000) g_input_max_age_ms = 1000;
        g_world_input_enabled = g_world_input_enabled ? 1 : 0;
        g_world_input_normalize = g_world_input_normalize ? 1 : 0;
        g_owner_submit_enabled = g_owner_submit_enabled ? 1 : 0;
        g_owner_tooltip_enabled = g_owner_tooltip_enabled ? 1 : 0;
        g_owner_all_window_calls = g_owner_all_window_calls ? 1 : 0;
        if(g_owner_submit_tolerance<1) g_owner_submit_tolerance=1;
        if(g_owner_submit_tolerance>24) g_owner_submit_tolerance=24;
        if(g_owner_submit_max_age_presents<1) g_owner_submit_max_age_presents=1;
        if(g_owner_submit_max_age_presents>240) g_owner_submit_max_age_presents=240;
        g_owner_input_remap_enabled = g_owner_input_remap_enabled ? 1 : 0;
        if(g_owner_input_max_age_presents<1) g_owner_input_max_age_presents=1;
        if(g_owner_input_max_age_presents>240) g_owner_input_max_age_presents=240;
        if(g_owner_input_exact_max_age_presents>32) g_owner_input_exact_max_age_presents=32;
        g_owner_scale_enabled = g_owner_submit_enabled;
        g_vtrace_enabled = g_vtrace_enabled ? 1 : 0;
        if(g_vtrace_capture_ms<500) g_vtrace_capture_ms=500; if(g_vtrace_capture_ms>10000) g_vtrace_capture_ms=10000;
        if(g_vtrace_slot_first>=VTRACE_SLOT_COUNT) g_vtrace_slot_first=0;
        if(g_vtrace_slot_last>=VTRACE_SLOT_COUNT) g_vtrace_slot_last=VTRACE_SLOT_COUNT-1;
        if(g_vtrace_slot_last<g_vtrace_slot_first) g_vtrace_slot_last=g_vtrace_slot_first;
    }
    g_ui_runtime_enabled = g_ui_enabled;
    g_input_runtime_enabled = g_input_enabled;
    log_uint("Font.Enabled=", (DWORD)g_font_enabled);
    log_uint("Font.AddSize=", (DWORD)g_font_add);
    log_uint("UI.SharpFilter=", (DWORD)g_ui_sharp_filter);
    log_uint("UI.KeepOnScreen=", (DWORD)g_ui_keep_on_screen);
    log_uint("Trace.Enabled=", (DWORD)g_trace_enabled);
    log_uint("Trace.CaptureMs=", g_trace_capture_ms);
    log_uint("UI.Enabled=", (DWORD)g_ui_enabled);
    log_uint("UI.ScalePercent=", (DWORD)g_ui_scale_percent);
    log_uint("UI.OriginX=", (DWORD)g_ui_origin_x);
    log_uint("UI.OriginY=", (DWORD)g_ui_origin_y);
    log_uint("UI.ScreenWidth=", (DWORD)g_ui_screen_w);
    log_uint("UI.ScreenHeight=", (DWORD)g_ui_screen_h);
    log_uint("UI.AnchorMode=", (DWORD)g_ui_anchor_mode);
    log_uint("UI.GroupGap=", (DWORD)g_ui_group_gap);
    log_uint("UI.MatchGap=", (DWORD)g_ui_match_gap);
    log_uint("UI.StableMatchGap=", (DWORD)g_ui_stable_match_gap);
    log_uint("UI.GlobalThresholdPercent=", (DWORD)g_ui_global_threshold_percent);
    log_uint("UI.ScaleGlobal=", (DWORD)g_ui_scale_global);
    log_uint("UI.ScaleUnmatched=", (DWORD)g_ui_scale_unmatched);
    log_uint("Input.Enabled=", (DWORD)g_input_enabled);
    log_uint("Input.HitRegionMaxAgeMs=", g_input_max_age_ms);
    log_uint("WorldInput.Enabled=", (DWORD)g_world_input_enabled);
    log_uint("WorldInput.NormalizeToScreen=", (DWORD)g_world_input_normalize);
    log_uint("OwnerSubmit.Enabled=", (DWORD)g_owner_submit_enabled);
    log_uint("OwnerBitmap.Enabled=", (DWORD)g_owner_bitmap_enabled);
    log_uint("OwnerSubmit.TooltipEnabled=", (DWORD)g_owner_tooltip_enabled);
    log_uint("OwnerSubmit.AllWindowCalls=", (DWORD)g_owner_all_window_calls);
    log_uint("OwnerSubmit.MatchTolerance=", g_owner_submit_tolerance);
    log_uint("OwnerSubmit.MaxAgePresents=", g_owner_submit_max_age_presents);
    log_uint("OwnerSubmit.OwnerInputEnabled=", (DWORD)g_owner_input_remap_enabled);
    log_uint("OwnerSubmit.OwnerInputGracePresents=", g_owner_input_max_age_presents);
    log_uint("OwnerSubmit.OwnerInputExactAgePresents=", g_owner_input_exact_max_age_presents);
    log_hex("OwnerSubmit.PositionXOffset=", g_owner_submit_pos_x_off);
    log_hex("OwnerSubmit.PositionYOffset=", g_owner_submit_pos_y_off);
    log_uint("VirtualTrace.Enabled=", (DWORD)g_vtrace_enabled);
    log_uint("VirtualTrace.CaptureMs=", g_vtrace_capture_ms);
    log_uint("VirtualTrace.SlotFirst=", g_vtrace_slot_first);
    log_uint("VirtualTrace.SlotLast=", g_vtrace_slot_last);
    exe = g_GetModuleHandleA ? g_GetModuleHandleA(0) : 0;
    g_exe = exe;
    if (exe) {
        text_hash = hash_text_section(exe, &ts, &image);
        log_hex("EXE.TimeDateStamp=", ts);
        log_hex("EXE.SizeOfImage=", image);
        g_exe_size = image;
        log_hex("EXE.TextFNV1a=", text_hash);
        if (ts == 0x5F4F3ABDUL && image == 0x011A3000UL)
            log_line("EXE build: PRM 2020-09-02 family (runtime .text hash may vary after relocations)");
        else
            log_line("EXE build: unknown; only validated import/COM hooks will be used");
    }
    ensure_real_winmm();
    log_line(g_real_winmm ? "Real WINMM: OK" : "Real WINMM: FAILED (fallback timing will be used)");
    install_font_hooks();
    install_phase2_hooks();
    install_input_hooks();
    install_world_input_hook();
    install_cursor_hooks();
    install_owner_bitmap_hooks();
    install_owner_hit_hooks();
    owner_submit_install_hooks();
    vtrace_install_submit_hooks();
    vtrace_install_active_vtables();
    log_line("Phase 3B armed: F2 settings; F3 UI filtering; F4 trace; F5 UI scale; F6 owner+2F mouse remap; F7 HUD groups; F8 diagnostics; F9 world input");
    log_line("Initialization complete");
}

static void ensure_initialized(void) {
    LONG expected;
    /* cmpxchg via compiler atomic; no CRT import. */
    expected = __atomic_load_n(&g_init_state, __ATOMIC_ACQUIRE);
    if (expected == 2) return;
    if (expected == 1) return; /* avoid re-entrant loader-lock deadlocks */
    expected = 0;
    if (__atomic_compare_exchange_n(&g_init_state, &expected, 1, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
        initialize_mod();
        __atomic_store_n(&g_init_state, 2, __ATOMIC_RELEASE);
    } else {
        while (__atomic_load_n(&g_init_state, __ATOMIC_ACQUIRE) != 2) { __asm__ volatile ("pause"); }
    }
}

/* ---------- DLL entry + exported WINMM forwards ---------- */
BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved) {
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        g_self = hinst;
        bootstrap_kernel32();
        if (g_DisableThreadLibraryCalls) g_DisableThreadLibraryCalls(hinst);
    }
    return TRUE;
}

MMRESULT WINAPI timeBeginPeriod(UINT period) {
    ensure_initialized();
    if (!g_real_timeBeginPeriod) ensure_real_winmm();
    return g_real_timeBeginPeriod ? g_real_timeBeginPeriod(period) : 0;
}

MMRESULT WINAPI timeEndPeriod(UINT period) {
    ensure_initialized();
    if (!g_real_timeEndPeriod) ensure_real_winmm();
    return g_real_timeEndPeriod ? g_real_timeEndPeriod(period) : 0;
}

MMRESULT WINAPI timeGetDevCaps(LPTIMECAPS caps, UINT size) {
    ensure_initialized();
    if (!g_real_timeGetDevCaps) ensure_real_winmm();
    if (g_real_timeGetDevCaps) return g_real_timeGetDevCaps(caps, size);
    if (caps && size >= sizeof(TIMECAPS)) { caps->wPeriodMin = 1; caps->wPeriodMax = 1000000; }
    return 0;
}

DWORD WINAPI timeGetTime(void) {
    ensure_initialized();
    if (!g_real_timeGetTime) ensure_real_winmm();
    if (g_real_timeGetTime) return g_real_timeGetTime();
    return g_GetTickCount ? g_GetTickCount() : 0;
}
