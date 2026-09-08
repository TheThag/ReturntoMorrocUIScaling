#ifndef PRM_UI_RESOLUTION_H
#define PRM_UI_RESOLUTION_H

/*
 * Bounded, non-executing reader for savedata/OptionInfo.lua.
 *
 * The savedata file is generated as one assignment per line.  This parser
 * intentionally accepts only literal assignments of the form
 *
 *     OptionInfoList["WIDTH"] = 3440;
 *     OptionInfoList['HEIGHT'] = 1440
 *
 * with whitespace, comments, and either quote style around the key.  It does
 * not execute Lua or evaluate expressions.  Lua short strings, long-bracket
 * strings, line comments, and long-bracket comments are skipped so text that
 * merely resembles an assignment cannot provide a resolution.  Unterminated
 * quoted/long-bracket tokens make the bounded input invalid.  Other Lua
 * syntax is not evaluated; callers should provide the generated assignment
 * format described above.
 */

static int ui_resolution_space(unsigned char c) {
    return c==' ' || c=='\t' || c=='\r' || c=='\n' || c=='\v' || c=='\f';
}

static int ui_resolution_identifier(unsigned char c) {
    return (c>='A' && c<='Z') || (c>='a' && c<='z') ||
           (c>='0' && c<='9') || c=='_';
}

static int ui_resolution_option_at(const char* text,DWORD length,DWORD at) {
    static const char name[]="OptionInfoList";
    DWORD i;
    if(!text || length<14 || at>length-14 ||
       (at && ui_resolution_identifier((unsigned char)text[at-1])) ||
       (at+14<length && ui_resolution_identifier((unsigned char)text[at+14]))) return 0;
    for(i=0;i<14;++i) if(text[at+i]!=name[i]) return 0;
    return 1;
}

/* Return the opener length for [=*[ and write the number of '=' characters. */
static DWORD ui_resolution_long_open(const char* text,DWORD length,DWORD at,DWORD* equals) {
    DWORD i,count=0;
    if(equals) *equals=0;
    if(!text || at>=length || text[at]!='[') return 0;
    i=at+1;
    while(i<length && text[i]=='=') { ++count; ++i; }
    if(i>=length || text[i]!='[') return 0;
    if(equals) *equals=count;
    return i-at+1;
}

static DWORD ui_resolution_skip_long(const char* text,DWORD length,DWORD at,
                                     DWORD* saw_newline,int* closed) {
    DWORD equals=0,open,i,j,count;
    if(saw_newline) *saw_newline=0;
    if(closed) *closed=0;
    open=ui_resolution_long_open(text,length,at,&equals);
    if(!open) return at;
    i=at+open;
    while(i<length) {
        if(text[i]=='\r' || text[i]=='\n') {
            if(saw_newline) *saw_newline=1;
        }
        if(text[i]==']') {
            j=i+1; count=0;
            while(j<length && text[j]=='=') { ++count; ++j; }
            if(count==equals && j<length && text[j]==']') {
                if(closed) *closed=1;
                return j+1;
            }
        }
        ++i;
    }
    return length;
}

static DWORD ui_resolution_skip_short(const char* text,DWORD length,DWORD at,
                                      DWORD* saw_newline,int* closed) {
    unsigned char quote; DWORD i;
    if(saw_newline) *saw_newline=0;
    if(closed) *closed=0;
    if(!text || at>=length || (text[at]!='\'' && text[at]!='"')) return at;
    quote=(unsigned char)text[at]; i=at+1;
    while(i<length) {
        if(text[i]=='\r' || text[i]=='\n') {
            if(saw_newline) *saw_newline=1;
        }
        if(text[i]=='\\') {
            ++i;
            if(i<length) {
                if(text[i]=='\r' || text[i]=='\n') {
                    if(saw_newline) *saw_newline=1;
                }
                ++i;
            }
            continue;
        }
        if(text[i]==quote) {
            if(closed) *closed=1;
            return i+1;
        }
        ++i;
    }
    return length;
}

/* Skip whitespace and Lua comments, reporting whether a line boundary was
 * crossed.  This is the only gap grammar accepted around target tokens. */
static DWORD ui_resolution_skip_gap(const char* text,DWORD length,DWORD at,
                                    int* saw_newline) {
    DWORD i=at,jump,nl;
    if(saw_newline) *saw_newline=0;
    for(;;) {
        while(i<length && ui_resolution_space((unsigned char)text[i])) {
            if(text[i]=='\r' || text[i]=='\n') if(saw_newline) *saw_newline=1;
            ++i;
        }
        if(i+1>=length || text[i]!='-' || text[i+1]!='-') break;
        i+=2;
        jump=ui_resolution_long_open(text,length,i,0);
        if(jump) {
            i=ui_resolution_skip_long(text,length,i,&nl,0);
            if(nl && saw_newline) *saw_newline=1;
        } else {
            while(i<length && text[i]!='\r' && text[i]!='\n') ++i;
        }
    }
    return i;
}

/* Stop a malformed target assignment at its semicolon or physical line end.
 * Strings/comments are skipped so their punctuation cannot terminate it. */
static DWORD ui_resolution_bad_end(const char* text,DWORD length,DWORD at) {
    DWORD i=at,jump,nl;
    while(i<length) {
        if(text[i]=='\r') return i+((i+1<length && text[i+1]=='\n')?2:1);
        if(text[i]=='\n') return i+1;
        if(text[i]==';') return i+1;
        if(i+1<length && text[i]=='-' && text[i+1]=='-') {
            i+=2; jump=ui_resolution_long_open(text,length,i,0);
            if(jump) i=ui_resolution_skip_long(text,length,i,&nl,0);
            else while(i<length && text[i]!='\r' && text[i]!='\n') ++i;
            continue;
        }
        if(text[i]=='\'' || text[i]=='"') {
            i=ui_resolution_skip_short(text,length,i,0,0); continue;
        }
        if(text[i]=='[' && ui_resolution_long_open(text,length,i,0)) {
            i=ui_resolution_skip_long(text,length,i,0,0); continue;
        }
        ++i;
    }
    return length;
}

/* Validate only the lexical regions that this bounded scanner skips.  This
 * catches a truncated tail even when both required assignments appeared
 * earlier in the buffer. */
static int ui_resolution_lexically_valid(const char* text,DWORD length) {
    DWORD i=0,nl; int closed;
    if(length>=3 && (unsigned char)text[0]==0xef &&
       (unsigned char)text[1]==0xbb && (unsigned char)text[2]==0xbf) i=3;
    while(i<length) {
        if(i+1<length && text[i]=='-' && text[i+1]=='-') {
            i+=2;
            if(ui_resolution_long_open(text,length,i,0)) {
                i=ui_resolution_skip_long(text,length,i,&nl,&closed);
                if(!closed) return 0;
            } else {
                while(i<length && text[i]!='\r' && text[i]!='\n') ++i;
            }
            continue;
        }
        if(text[i]=='\'' || text[i]=='"') {
            i=ui_resolution_skip_short(text,length,i,&nl,&closed);
            if(!closed) return 0;
            continue;
        }
        if(text[i]=='[' && ui_resolution_long_open(text,length,i,0)) {
            i=ui_resolution_skip_long(text,length,i,&nl,&closed);
            if(!closed) return 0;
            continue;
        }
        ++i;
    }
    return 1;
}

/* Return 1 when an OptionInfoList[...] form was consumed.  target is 1 for
 * WIDTH, 2 for HEIGHT, and 0 for another key.  A recognized target form is
 * consumed even when invalid, so a later malformed duplicate cannot leave an
 * earlier valid value silently active. */
static int ui_resolution_assignment_at(const char* text,DWORD length,DWORD at,
                                       DWORD* next,int* target,int* valid,
                                       LONG* value) {
    DWORD i,key_len=0,after_gap;
    unsigned char quote,c; int gap_newline=0,closed=0,key_width=1,key_height=1;
    DWORD parsed=0; int overflow=0;
    if(next) *next=at+1;
    if(target) *target=0;
    if(valid) *valid=0;
    if(value) *value=0;
    if(!ui_resolution_option_at(text,length,at)) return 0;
    i=at+14;
    i=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(i>=length || text[i]!='[') return 0;
    ++i;
    i=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(i>=length || (text[i]!='\'' && text[i]!='"')) {
        if(next) *next=ui_resolution_bad_end(text,length,i);
        return 1;
    }
    quote=(unsigned char)text[i++];
    while(i<length) {
        c=(unsigned char)text[i];
        if(c==quote) { closed=1; ++i; break; }
        if(c=='\\') {
            key_width=key_height=0; ++i;
            if(i<length) ++i;
            continue;
        }
        if(key_len>=5 || c!="WIDTH"[key_len]) key_width=0;
        if(key_len>=6 || c!="HEIGHT"[key_len]) key_height=0;
        ++key_len; ++i;
    }
    if(key_len!=5) key_width=0;
    if(key_len!=6) key_height=0;
    if(target) *target=key_width?1:(key_height?2:0);
    if(!closed) {
        if(next) *next=ui_resolution_bad_end(text,length,i);
        return 1;
    }
    i=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(i>=length || text[i]!=']') {
        if(next) *next=ui_resolution_bad_end(text,length,i);
        return 1;
    }
    ++i;
    i=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(i>=length || text[i]!='=' || (i+1<length && text[i+1]=='=')) {
        if(next) *next=ui_resolution_bad_end(text,length,i);
        return 1;
    }
    ++i;
    i=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(i>=length || text[i]<'0' || text[i]>'9') {
        if(next) *next=ui_resolution_bad_end(text,length,i);
        return 1;
    }
    while(i<length && text[i]>='0' && text[i]<='9') {
        if(parsed>16384UL || (parsed==16384UL && text[i]>'0')) overflow=1;
        if(!overflow) parsed=parsed*10UL+(DWORD)(text[i]-'0');
        ++i;
    }
    after_gap=ui_resolution_skip_gap(text,length,i,&gap_newline);
    if(after_gap<length && text[after_gap]==';') {
        if(next) *next=after_gap+1;
    } else if(after_gap==length || gap_newline) {
        if(next) *next=after_gap;
    } else {
        if(next) *next=ui_resolution_bad_end(text,length,after_gap);
        return 1;
    }
    if(overflow || (key_width && (parsed<640UL || parsed>16384UL)) ||
       (key_height && (parsed<480UL || parsed>16384UL))) return 1;
    if(valid) *valid=1;
    if(value) *value=(LONG)parsed;
    return 1;
}

/* Parse into locals first.  On every failure, including a bad duplicate, the
 * caller's output pair remains byte-for-byte unchanged. */
static int ui_resolution_parse(const char* text,DWORD length,LONG* width,LONG* height) {
    DWORD i=0,next; int target,valid,width_seen=0,height_seen=0;
    int width_valid=0,height_valid=0; LONG value,width_value=0,height_value=0;
    if(!text || !width || !height) return 0;
    if(!ui_resolution_lexically_valid(text,length)) return 0;
    if(length>=3 && (unsigned char)text[0]==0xef && (unsigned char)text[1]==0xbb && (unsigned char)text[2]==0xbf) i=3;
    while(i<length) {
        if(i+1<length && text[i]=='-' && text[i+1]=='-') {
            i=ui_resolution_skip_gap(text,length,i,0); continue;
        }
        if(text[i]=='\'' || text[i]=='"') {
            i=ui_resolution_skip_short(text,length,i,0,0); continue;
        }
        if(text[i]=='[' && ui_resolution_long_open(text,length,i,0)) {
            i=ui_resolution_skip_long(text,length,i,0,0); continue;
        }
        if(ui_resolution_option_at(text,length,i)) {
            if(ui_resolution_assignment_at(text,length,i,&next,&target,&valid,&value)) {
                if(target==1) {
                    width_seen=1; width_valid=valid; if(valid) width_value=value;
                } else if(target==2) {
                    height_seen=1; height_valid=valid; if(valid) height_value=value;
                }
                i=next>i?next:i+1; continue;
            }
        }
        ++i;
    }
    if(!width_seen || !height_seen || !width_valid || !height_valid) return 0;
    *width=width_value; *height=height_value; return 1;
}

#endif /* PRM_UI_RESOLUTION_H */
