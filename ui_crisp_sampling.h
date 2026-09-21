#ifndef UI_CRISP_SAMPLING_H
#define UI_CRISP_SAMPLING_H
/* Resolve POINT-sampling ties consistently across the two triangles of an
 * axis-aligned UI rectangle. Bias texture coordinates by 1/64 screen pixel,
 * never geometry. This is a tie-break, not a half-texel alignment correction.
 * Operates only on the draw-local copy after point filtering was enabled. */
static int ui_crisp_bias_quad(unsigned int fvf, void* vertices, unsigned int count) {
    float (*v)[8]=(float (*)[8])vertices;
    float l,r,t,b,du,dv; unsigned int i,mask=0,tl=0,tr=0,bl=0;
    if(fvf!=0x1c4 || count!=4 || !vertices) return 0;
    l=r=v[0][0];t=b=v[0][1];
    for(i=0;i<4;++i) {
        /* Ordered comparisons reject NaNs and unreasonable/infinite inputs. */
        if(!(v[i][0]>=-65536 && v[i][0]<=65536 && v[i][1]>=-65536 && v[i][1]<=65536 &&
             v[i][6]>=-16 && v[i][6]<=16 && v[i][7]>=-16 && v[i][7]<=16 &&
             v[i][3]>0 && v[i][3]<=10000)) return 0;
        if(v[i][2]!=v[0][2] || v[i][3]!=v[0][3]) return 0;
        if(v[i][0]<l)l=v[i][0];if(v[i][0]>r)r=v[i][0];
        if(v[i][1]<t)t=v[i][1];if(v[i][1]>b)b=v[i][1];
    }
    if(r-l<1 || b-t<1) return 0;
    for(i=0;i<4;++i) {
        unsigned int corner;
        if((v[i][0]!=l && v[i][0]!=r) || (v[i][1]!=t && v[i][1]!=b)) return 0;
        corner=(v[i][0]==r?1:0)|(v[i][1]==b?2:0);
        mask|=1u<<corner;
        if(corner==0)tl=i;else if(corner==1)tr=i;else if(corner==2)bl=i;
    }
    if(mask!=15) return 0;
    for(i=0;i<4;++i) {
        if(v[i][6]!=(v[i][0]==l?v[tl][6]:v[tr][6]) ||
           v[i][7]!=(v[i][1]==t?v[tl][7]:v[bl][7])) return 0;
    }
    du=(v[tr][6]-v[tl][6])/(r-l)*(1.0f/64.0f);
    dv=(v[bl][7]-v[tl][7])/(b-t)*(1.0f/64.0f);
    if(du==0 && dv==0) return 0;
    for(i=0;i<4;++i) {v[i][6]+=du;v[i][7]+=dv;}
    return 1;
}
#endif
