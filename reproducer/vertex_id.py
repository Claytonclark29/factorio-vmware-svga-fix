# SPDX-License-Identifier: MIT
"""Standalone publication adaptation; GL run not repeated after adaptation.
No game assets. Only call main with --execute-rendering in an approved test session.
Original project test code is MIT licensed; see LICENSE and LICENSES/README.md.
"""
import argparse
import sys


def run(suite, expected_renderer):
    """Minimal GLX/OpenGL indexed vertex-ID test. No game assets or tracing."""
    import ctypes as C
    import json
    import struct
    from collections import Counter

    X=C.CDLL('libX11.so.6')
    GL=C.CDLL('libGL.so.1')
    P=C.c_void_p; I=C.c_int; U=C.c_uint; F=C.c_float
    def bind(lib,name,restype,args):
        f=getattr(lib,name);f.restype=restype;f.argtypes=args;return f
    open_display=bind(X,'XOpenDisplay',P,[C.c_char_p])
    default_screen=bind(X,'XDefaultScreen',I,[P])
    free=bind(X,'XFree',I,[P])
    close_display=bind(X,'XCloseDisplay',I,[P])
    choose=bind(GL,'glXChooseFBConfig',C.POINTER(P),[P,I,C.POINTER(I),C.POINTER(I)])
    getproc=bind(GL,'glXGetProcAddressARB',P,[C.c_char_p])
    create_pbuffer=bind(GL,'glXCreatePbuffer',C.c_ulong,[P,P,C.POINTER(I)])
    make_current=bind(GL,'glXMakeContextCurrent',I,[P,C.c_ulong,C.c_ulong,P])
    destroy_pbuffer=bind(GL,'glXDestroyPbuffer',None,[P,C.c_ulong])
    destroy_context=bind(GL,'glXDestroyContext',None,[P,P])
    def gl(name,restype,args):
        address=getproc(name.encode());assert address,name
        return C.CFUNCTYPE(restype,*args)(address)

    dpy=open_display(None);assert dpy,'No X display'
    attrs=(I*15)(0x8012,1,0x8010,4,0x8011,1,8,8,9,8,10,8,11,8,0)
    count=I();configs=choose(dpy,default_screen(dpy),attrs,C.byref(count));assert count.value
    config=configs[0]
    context_create=gl('glXCreateContextAttribsARB',P,[P,P,P,I,C.POINTER(I)])
    context_attrs=(I*7)(0x2091,3,0x2092,3,0x9126,1,0)
    ctx=context_create(dpy,config,None,1,context_attrs);assert ctx,'Context creation failed'
    pbattrs=(I*5)(0x8041,64,0x8040,64,0)
    pb=create_pbuffer(dpy,config,pbattrs);assert pb
    assert make_current(dpy,pb,pb,ctx)
    free(configs)

    get_string=gl('glGetString',C.c_char_p,[U])
    get_integer=gl('glGetIntegerv',None,[U,C.POINTER(I)])
    get_error=gl('glGetError',U,[])
    create_shader=gl('glCreateShader',U,[U])
    shader_source=gl('glShaderSource',None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)])
    compile_shader=gl('glCompileShader',None,[U])
    get_shader=gl('glGetShaderiv',None,[U,U,C.POINTER(I)])
    shader_log=gl('glGetShaderInfoLog',None,[U,I,C.POINTER(I),C.c_char_p])
    create_program=gl('glCreateProgram',U,[])
    attach_shader=gl('glAttachShader',None,[U,U])
    link_program=gl('glLinkProgram',None,[U])
    get_program=gl('glGetProgramiv',None,[U,U,C.POINTER(I)])
    program_log=gl('glGetProgramInfoLog',None,[U,I,C.POINTER(I),C.c_char_p])
    use_program=gl('glUseProgram',None,[U])
    gen_vao=gl('glGenVertexArrays',None,[I,C.POINTER(U)])
    bind_vao=gl('glBindVertexArray',None,[U])
    gen_buffers=gl('glGenBuffers',None,[I,C.POINTER(U)])
    bind_buffer=gl('glBindBuffer',None,[U,U])
    buffer_data=gl('glBufferData',None,[U,C.c_ssize_t,P,U])
    enable_attrib=gl('glEnableVertexAttribArray',None,[U])
    attrib_pointer=gl('glVertexAttribPointer',None,[U,I,U,C.c_ubyte,I,P])
    attrib_ipointer=gl('glVertexAttribIPointer',None,[U,I,U,I,P])
    gen_textures=gl('glGenTextures',None,[I,C.POINTER(U)])
    bind_texture=gl('glBindTexture',None,[U,U])
    tex_image=gl('glTexImage2D',None,[U,I,I,I,I,I,U,U,P])
    gen_fbo=gl('glGenFramebuffers',None,[I,C.POINTER(U)])
    bind_fbo=gl('glBindFramebuffer',None,[U,U])
    framebuffer_texture=gl('glFramebufferTexture2D',None,[U,U,U,U,I])
    check_fbo=gl('glCheckFramebufferStatus',U,[U])
    draw_buffer=gl('glDrawBuffer',None,[U])
    read_buffer=gl('glReadBuffer',None,[U])
    viewport=gl('glViewport',None,[I,I,I,I])
    disable=gl('glDisable',None,[U])
    provoking=gl('glProvokingVertex',None,[U])
    clear=gl('glClearBufferuiv',None,[U,I,C.POINTER(U)])
    draw=gl('glDrawElements',None,[U,I,U,P])
    read_pixels=gl('glReadPixels',None,[I,I,I,I,U,U,P])
    finish=gl('glFinish',None,[])

    vs=b'''#version 330 core
    layout(location=0) in vec2 position;
    layout(location=1) in uint explicitVertexID;
    layout(location=2) in uint explicitInstanceID;
    uniform int instanceCount;
    flat out uvec4 evidence;
    void main(){
        uint corner=(position.x>0.0?2u:0u)|(position.y>0.0?1u:0u);
        evidence=uvec4(uint(gl_VertexID),explicitVertexID,corner+explicitInstanceID*256u,uint(gl_InstanceID)+1u);
        float n=float(instanceCount);
        gl_Position=vec4((position.x+2.0*float(gl_InstanceID)+1.0-n)/n,position.y,0.0,1.0);
    }'''
    fs=b'''#version 330 core
    flat in uvec4 evidence;
    layout(location=0) out uvec4 result;
    void main(){result=evidence;}'''
    program=create_program()
    for kind,source in [(0x8B31,vs),(0x8B30,fs)]:
        shader=create_shader(kind);p=C.c_char_p(source)
        shader_source(shader,1,C.byref(p),None);compile_shader(shader)
        ok=I();get_shader(shader,0x8B81,C.byref(ok))
        if not ok.value:
            log=C.create_string_buffer(8192);shader_log(shader,8192,None,log);raise RuntimeError(log.value.decode())
        attach_shader(program,shader)
    link_program(program);ok=I();get_program(program,0x8B82,C.byref(ok))
    if not ok.value:
        log=C.create_string_buffer(8192);program_log(program,8192,None,log);raise RuntimeError(log.value.decode())
    use_program(program)
    vao=U();gen_vao(1,C.byref(vao));bind_vao(vao)
    buffers=(U*3)();gen_buffers(3,buffers)
    vertices=b''.join(struct.pack('<ffI',x,y,i) for i,(x,y) in enumerate([(-.8,-.8),(-.8,.8),(.8,-.8),(.8,.8)]))
    vdata=C.create_string_buffer(vertices)
    bind_buffer(0x8892,buffers[0]);buffer_data(0x8892,len(vertices),vdata,0x88E4)
    enable_attrib(0);attrib_pointer(0,2,0x1406,0,12,P(0))
    enable_attrib(1);attrib_ipointer(1,1,0x1405,12,P(8))
    bind_buffer(0x8893,buffers[1])
    tex=U();gen_textures(1,C.byref(tex));bind_texture(0x0DE1,tex)
    tex_image(0x0DE1,0,0x8D70,64,64,0,0x8D99,0x1405,None) # RGBA32UI
    fbo=U();gen_fbo(1,C.byref(fbo));bind_fbo(0x8D40,fbo)
    framebuffer_texture(0x8D40,0x8CE0,0x0DE1,tex,0)
    assert check_fbo(0x8D40)==0x8CD5,'Framebuffer incomplete'
    draw_buffer(0x8CE0);read_buffer(0x8CE0);viewport(0,0,64,64)
    for cap in [0x0BE2,0x0BD0,0x0B71,0x0B44,0x0C11,0x809D,0x8DB9]:disable(cap)
    provoking(0x8E4E) # GL_LAST_VERTEX_CONVENTION
    convention=I();get_integer(0x8E4F,C.byref(convention));assert convention.value==0x8E4E
    assert get_error()==0,'Setup GL error'

    arrays=gl('glDrawArrays',None,[U,I,I])
    elements_base=gl('glDrawElementsBaseVertex',None,[U,I,U,P,I])
    arrays_inst=gl('glDrawArraysInstanced',None,[U,I,I,I])
    elements_inst=gl('glDrawElementsInstancedBaseVertex',None,[U,I,U,P,I,I])
    arrays_baseinst=gl('glDrawArraysInstancedBaseInstance',None,[U,I,I,I,U])
    elements_baseinst=gl('glDrawElementsInstancedBaseVertexBaseInstance',None,[U,I,U,P,I,I,U])
    attrib_divisor=gl('glVertexAttribDivisor',None,[U,U])
    uniform_location=gl('glGetUniformLocation',I,[U,C.c_char_p])
    uniform_i=gl('glUniform1i',None,[I,I])
    instance_count_location=uniform_location(program,b'instanceCount');assert instance_count_location>=0
    bind_buffer(0x8892,buffers[2]);idata=(U*16)(*range(16));buffer_data(0x8892,C.sizeof(idata),idata,0x88E4)
    enable_attrib(2);attrib_ipointer(2,1,0x1405,4,P(0));attrib_divisor(2,1)
    result={'renderer':get_string(0x1F01).decode(),'vendor':get_string(0x1F00).decode(),'version':get_string(0x1F02).decode(),'encoding':'RGBA32UI: builtin vertex ID, explicit vertex attribute ID, corner+256*divisor1 instance attribute, gl_InstanceID+1','cases':[]}
    assert int(result['version'].split('.')[0])>=4,'Fixture requires GL4'
    assert expected_renderer in result['renderer'],'Unexpected renderer'
    result.update(suite=suite,publication_adaptation=True,draw_budget=1 if suite=='minimal' else 180,shader_compilations=2,program_links=1)

    sentinel=(U*4)(0xffffffff,0xffffffff,0xffffffff,0)
    pixels=(U*(64*64*4))()
    cases=[]
    def add(kind='elements',width=4,offset=0,base=0,first=0,n=1,baseinstance=0,convention='last',pattern='quad',group='basic'):
        cases.append(dict(kind=kind,width=width,offset=offset,base=base,first=first,instances=n,baseinstance=baseinstance,convention=convention,pattern=pattern,group=group))
    # Index-width/offset/base-vertex cross product, all nonnegative effective indices.
    for width in [1,2,4]:
     for offset in [0,1,2,3,4,17,14994]:
      for base in [0,5,-5]:add(width=width,offset=offset,base=base,group='indexed-offset-width-base')
    # Nonmonotonic indices, all four corner observations under both provoking modes.
    for width in [1,2,4]:
     for convention in ['first','last']:
      add(width=width,offset=3,pattern='permuted',convention=convention,group='index-order-provoking')
    # Array first must remain included.
    for first in [0,1,2,3,4,17]:
     for convention in ['first','last']:add(kind='arrays',first=first,convention=convention,group='arrays-first')
    # Instancing and base-instance alter neither vertex identity nor gl_InstanceID.
    for width in [1,2,4]:
     for offset in [0,1,3,17]:
      for base in [0,5,-5]:
       for bi in [0,3]:add(kind='elements-instanced',width=width,offset=offset,base=base,n=3,baseinstance=bi,group='indexed-instancing')
    for first in [0,1,17]:
     for bi in [0,3]:add(kind='arrays-instanced',first=first,n=3,baseinstance=bi,group='array-instancing')
    # Adjacent calls alternate draw kind and bias, including transitions back to zero.
    for repeat in range(3):
     add(kind='arrays',first=17,group='state-transition')
     add(offset=3,base=-5,group='state-transition')
     add(kind='arrays',first=0,group='state-transition')
     add(offset=17,base=5,group='state-transition')
     add(offset=0,base=0,group='state-transition')
     add(kind='arrays-instanced',first=4,n=2,baseinstance=3,group='state-transition')
     add(offset=1,base=0,group='state-transition')
    if suite == 'minimal':
        cases=[c for c in cases if c['kind']=='elements' and c['width']==2 and c['offset']==17 and c['base']==0 and c['group']=='indexed-offset-width-base']
        assert len(cases)==1
    else:
        assert len(cases)==180
    corner_positions=[(-.8,-.8),(-.8,.8),(.8,-.8),(.8,.8)]
    for number,case in enumerate(cases):
        kind=case['kind'];base=case['base'];offset=case['offset'];width=case['width'];first=case['first'];n=case['instances'];bi=case['baseinstance'];is_arrays=kind.startswith('arrays')
        provoking(0x8E4D if case['convention']=='first' else 0x8E4E)
        declared=I();get_integer(0x8E4F,C.byref(declared));assert declared.value==(0x8E4D if case['convention']=='first' else 0x8E4E)
        if is_arrays:
            vertices=[(0.0,0.0,i) for i in range(first+6)]
            order=[0,1,2,2,1,3]
            for j,corner in enumerate(order):vertices[first+j]=(*corner_positions[corner],first+j)
            effective=list(range(first,first+6));corners=order;indices=None
        else:
            raw=[0,1,2,2,1,3] if case['pattern']=='quad' else [7,2,5,5,2,9]
            raw=[i+max(0,-base) for i in raw];effective=[i+base for i in raw];assert min(effective)>=0
            corner_for_id={effective[0]:0,effective[1]:1,effective[2]:2,effective[5]:3}
            vertices=[(0.0,0.0,i) for i in range(max(effective)+1)]
            for i,corner in corner_for_id.items():vertices[i]=(*corner_positions[corner],i)
            corners=[corner_for_id[i] for i in effective];indices=raw
        vbytes=b''.join(struct.pack('<ffI',*v) for v in vertices);vdata=C.create_string_buffer(vbytes)
        bind_buffer(0x8892,buffers[0]);buffer_data(0x8892,len(vbytes),vdata,0x88E4)
        bind_buffer(0x8893,buffers[1])
        if not is_arrays:
            fmt={1:'B',2:'H',4:'I'}[width];index_type={1:0x1401,2:0x1403,4:0x1405}[width]
            payload=bytes(offset*width)+struct.pack('<6'+fmt,*indices);data=C.create_string_buffer(payload);buffer_data(0x8893,len(payload),data,0x88E4)
        uniform_i(instance_count_location,n);clear(0x1800,0,sentinel)
        if kind=='arrays':arrays(0x0004,first,6)
        elif kind=='arrays-instanced':
            if bi:arrays_baseinst(0x0004,first,6,n,bi)
            else:arrays_inst(0x0004,first,6,n)
        elif kind=='elements-instanced':
            if bi:elements_baseinst(0x0004,6,index_type,P(offset*width),n,base,bi)
            else:elements_inst(0x0004,6,index_type,P(offset*width),n,base)
        elif base:elements_base(0x0004,6,index_type,P(offset*width),base)
        else:draw(0x0004,6,index_type,P(offset*width))
        finish();read_pixels(0,0,64,64,0x8D99,0x1405,pixels);error=get_error();assert error==0,hex(error)
        seen=Counter(tuple(pixels[i:i+4]) for i in range(0,len(pixels),4) if pixels[i+3]!=0)
        pv=[0,3] if case['convention']=='first' else [2,5]
        expected={(effective[j],effective[j],corners[j]+256*(inst+bi),inst+1) for inst in range(n) for j in pv}
        observed=set(seen);passed=observed==expected
        result['cases'].append(dict(case,case_number=number,indices=indices,expected=[list(x) for x in sorted(expected)],observations=[{'values':list(x),'pixels':count} for x,count in sorted(seen.items())],passed=passed,gl_error=error))
    
    make_current(dpy,0,0,None);destroy_pbuffer(dpy,pb);destroy_context(dpy,ctx);close_display(dpy)
    result['normal_cleanup']=True;
    print(json.dumps(result,indent=2))
    return 0 if all(c["passed"] for c in result["cases"]) else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-rendering', action='store_true')
    parser.add_argument('--suite', choices=['minimal','regression'], default='minimal')
    parser.add_argument('--expect-renderer', required=True, help='Expected renderer substring, e.g. SVGA or llvmpipe')
    args=parser.parse_args()
    if not args.execute_rendering:
        parser.error('No rendering requested; --execute-rendering is required')
    if sys.flags.optimize:
        parser.error('Assertions are required; do not use Python -O')
    return run(args.suite,args.expect_renderer)


if __name__=='__main__':
    raise SystemExit(main())
