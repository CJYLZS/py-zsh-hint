PWD=$(pwd)
cd $(dirname $0)
if [ ! -f /usr/bin/pyhint ]; then
    sudo ln -s $(pwd)/pyhint /usr/bin/pyhint
fi
cd $PWD

function py_hint(){
    # emulate -L zsh
    LBUFFER=$(LINES=${LINES} COLUMNS=${COLUMNS} BUFFER=${LBUFFER} ALIAS=$(alias) pyhint)
    RET=$?
    CURSOR=$#BUFFER
    if [[ $RET -eq 0 || $RET -eq 3 ]]; then
        zle -R -c
    elif [[ $RET -eq 1 ]]; then
        echo -n '\n'
        eval $BUFFER </dev/tty
        BUFFER=''
        print -Pn $PROMPT
        zle -R -c
    fi
}

zle -N py_hint

bindkey '^U' py_hint
