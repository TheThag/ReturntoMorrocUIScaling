"""Exercise the production UV tie-break with a float32 two-triangle sampler.
This models interpolation sensitivity; it is not a GPU or in-game capture.
"""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "ui_crisp_sampling.h"
static float q[4][8],original[4][8];
static void setup(float scale,float uv_start) {
 memset(q,0,sizeof(q));
 for(int i=0;i<4;i++) {
  q[i][0]=(i&1)*256*scale;q[i][1]=(i>>1)*180*scale;
  q[i][3]=0.99999f;q[i][6]=(uv_start+(i&1)*256)/256;
  q[i][7]=(uv_start+(i>>1)*180)/256;
 }
 memcpy(original,q,sizeof(q));
}
static float sample(float v[4][8],int x,int y,float scale) {
 float a=x/(256*scale),b=y/(180*scale),l[3];int ids[3];
 if(a+b<=1) {l[0]=1-a-b;l[1]=a;l[2]=b;ids[0]=0;ids[1]=1;ids[2]=2;}
 else {l[0]=a+b-1;l[1]=1-b;l[2]=1-a;ids[0]=3;ids[1]=1;ids[2]=2;}
 float uv=0,rhw=0;
 for(int i=0;i<3;i++) {uv+=l[i]*v[ids[i]][7]*v[ids[i]][3];rhw+=l[i]*v[ids[i]][3];}
 return uv/rhw*256;
}
int main(void) {
 int total_before=0;
 for(int scale=1;scale<=10;scale++) for(int convention=0;convention<2;convention++) {
  float start=convention?0.5f:0;setup(scale,start);
  assert(ui_crisp_bias_quad(0x1c4,q,4));
  for(int i=0;i<4;i++)assert(!memcmp(q[i],original[i],6*sizeof(float)));
  int before=0,after=0;
  for(int y=0;y<180*scale;y++) for(int x=0;x<256*scale;x++) {
   int expected=(int)floor((double)start+(double)y/scale);
   before+=(int)floorf(sample(original,x,y,scale))!=expected;
   after+=(int)floorf(sample(q,x,y,scale))!=expected;
  }
  total_before+=before;
  if(after)printf("scale=%d convention=%d errors=%d\n",scale,convention,after);
  assert(!after);
 }
 assert(total_before>0);
 /* Fractional scales, fractional origins, flipped UVs: constant subpixel bias,
    and every non-UV field remains byte-identical. */
 float scales[]={1,1.3f,1.5f,2.75f,10};
 for(int j=0;j<5;j++) {
  setup(scales[j],.5f);
  for(int i=0;i<4;i++){q[i][0]+=10.3f;q[i][1]-=27.25f;q[i][6]=1-q[i][6];}
  memcpy(original,q,sizeof(q));assert(ui_crisp_bias_quad(0x1c4,q,4));
  for(int i=0;i<4;i++) {
   assert(!memcmp(q[i],original[i],24));
   assert(fabsf((q[i][6]-original[i][6])*256*scales[j]+1.0f/64)<.001f);
  }
 }
 /* Cooldowns (triangle counts), malformed/rotated and perspective quads bypass. */
 for(int n=0;n<=24;n++)if(n!=4){setup(2,.5f);assert(!ui_crisp_bias_quad(0x1c4,q,n));assert(!memcmp(q,original,sizeof(q)));}
 setup(2,.5f);assert(!ui_crisp_bias_quad(0x144,q,4));
 for(int c=0;c<4;c++) {
  setup(2,.5f);
  if(c==0)q[1][1]+=1;if(c==1)q[1][3]=.5f;if(c==2)q[1][0]=NAN;if(c==3)q[3][6]+=.1f;
  memcpy(original,q,sizeof(q));assert(!ui_crisp_bias_quad(0x1c4,q,4));assert(!memcmp(q,original,sizeof(q)));
 }
 printf("PASS: resolved %d synthetic point-sampling disagreements; geometry preserved; fractional/flipped UVs; cooldown and unsupported-draw exclusions\n",total_before);
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['clang','-std=c11','-O1','-ffp-contract=off','-fsanitize=address,undefined','-I',str(root),str(p/'test.c'),'-lm','-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
