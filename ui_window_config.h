#ifndef PRM_UI_WINDOW_CONFIG_H
#define PRM_UI_WINDOW_CONFIG_H

/* Stable per-type preferences. Zero percent inherits the global default.
 * Runtime object pointers never become persistent keys. */
#define UI_WINDOW_CONFIG_CAP 256
#define UI_WINDOW_NAME_CAP 72
#define UI_WINDOW_OFFSET_LIMIT 8192
#ifndef UI_WINDOW_READ
#define UI_WINDOW_READ(section,key,fallback) (fallback)
#endif

typedef struct {
    char name[UI_WINDOW_NAME_CAP];
    int percent,x,y;
} UIWindowConfig;
static UIWindowConfig g_ui_window_configs[UI_WINDOW_CONFIG_CAP];
static unsigned int g_ui_window_config_count;

static inline int ui_window_clamp_offset(int value) {
    if(value < -UI_WINDOW_OFFSET_LIMIT) return -UI_WINDOW_OFFSET_LIMIT;
    if(value > UI_WINDOW_OFFSET_LIMIT) return UI_WINDOW_OFFSET_LIMIT;
    return value;
}
static inline int ui_window_valid_percent(int value) {
    return value==0 || (value>=100 && value<=1000);
}
static inline void ui_window_section(const char* name,char* out) {
    unsigned int i=0,j=0; const char* prefix="Window.";
    while(prefix[i]) { out[i]=prefix[i];++i; }
    while(name[j] && j<UI_WINDOW_NAME_CAP-1) out[i++]=name[j++];
    out[i]=0;
}
static inline UIWindowConfig* ui_window_config(const char* name,int create) {
    unsigned int i,j; UIWindowConfig* c; char section[UI_WINDOW_NAME_CAP+8];
    if(!name || !name[0]) return 0;
    for(j=0;name[j];++j) if(j>=UI_WINDOW_NAME_CAP-1) return 0;
    for(i=0;i<g_ui_window_config_count;++i) {
        c=&g_ui_window_configs[i];
        for(j=0;name[j] && name[j]==c->name[j];++j) {}
        if(!name[j] && !c->name[j]) return c;
    }
    if(!create || g_ui_window_config_count==UI_WINDOW_CONFIG_CAP) return 0;
    c=&g_ui_window_configs[g_ui_window_config_count++];
    for(j=0;name[j];++j) c->name[j]=name[j];
    c->name[j]=0;ui_window_section(name,section);
    c->percent=(int)UI_WINDOW_READ(section,"ScalePercent",0);
    if(!ui_window_valid_percent(c->percent)) c->percent=0;
    c->x=ui_window_clamp_offset((int)UI_WINDOW_READ(section,"OffsetX",0));
    c->y=ui_window_clamp_offset((int)UI_WINDOW_READ(section,"OffsetY",0));
    return c;
}
static inline int ui_window_custom(const char* name) {
    UIWindowConfig* c=ui_window_config(name,0);
    return c && (c->percent || c->x || c->y);
}
static inline int ui_window_percent(const char* name,int global) {
    UIWindowConfig* c=ui_window_config(name,1);
    return c && c->percent?c->percent:global;
}
static inline int ui_window_set(const char* name,int percent,int x,int y) {
    UIWindowConfig* c;
    if(!ui_window_valid_percent(percent)) return 0;
    c=ui_window_config(name,1);if(!c) return 0;
    c->percent=percent;c->x=ui_window_clamp_offset(x);c->y=ui_window_clamp_offset(y);
    return 1;
}
#endif
