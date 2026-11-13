# ~/.config/fish/config.fish

if status is-interactive
    bind ctrl-c 'commandline -f cancel-commandline repaint'
    bind ctrl-left backward-word
    bind ctrl-right forward-word

    function push-lineageos-update --wraps='~/Projects/lineage-nio/packages/apps/Updater/push-update.sh'
        ~/Projects/lineage-nio/packages/apps/Updater/push-update.sh $argv
    end

    function update-proxy-config --wraps='sudo python ~/Projects/env/proxy/update-config.py'
        sudo python ~/Projects/env/proxy/update-config.py $argv
    end

    function __sandbox_launch
        # ccache 目录在 agent sandbox 里不可写，关掉
        set -l unset_envs \
            USE_CCACHE \
            CCACHE_EXEC \
            CMAKE_C_COMPILER_LAUNCHER \
            CMAKE_CXX_COMPILER_LAUNCHER \
            RUSTC_WRAPPER
        set -l hidden_dirs \
            .opencode-data \
            .dsh-data

        # argv 按第一个 `--` 切成两段：前半是 bwrap 额外参数，后半是要跑的命令。
        # 第一个 `--` 之后的 `--` 原样保留给命令行。
        set -l extra
        set -l cmd
        set -l in_cmd 0
        for a in $argv
            if test "$a" = '--'; and test $in_cmd -eq 0
                set in_cmd 1
            else if test $in_cmd -eq 1
                set -a cmd $a
            else
                set -a extra $a
            end
        end

        set -l args \
            --unshare-all \
            --die-with-parent \
            --share-net \
            --tmpfs / \
            --dev /dev \
            --proc /proc \
            --tmpfs /tmp \
            --ro-bind /usr /usr \
            --ro-bind /opt /opt \
            --ro-bind /etc /etc \
            --ro-bind /bin /bin \
            --ro-bind /lib /lib \
            --ro-bind /lib64 /lib64 \
            --tmpfs /etc/ssh/ssh_config.d

        set -a args --bind . /w

        for e in $unset_envs
            set -a args --unsetenv $e
        end

        # 仅当目录存在于 cwd 时才用 tmpfs 遮挡
        for d in $hidden_dirs
            if test -e $d
                set -a args --tmpfs /w/$d
            end
        end

        set -a args $extra

        bwrap $args --chdir /w -- $cmd
    end

    function opencode-here
        mkdir -p .opencode-data/{cache,config,share,state}
        __sandbox_launch \
            --bind     .opencode-data/cache  $HOME/.cache/opencode \
            --bind     .opencode-data/config $HOME/.config/opencode \
            --bind     .opencode-data/share  $HOME/.local/share/opencode \
            --bind     .opencode-data/state  $HOME/.local/state/opencode \
            --bind-try .opencode-data/ssh    $HOME/.ssh \
            -- \
            bash -c 'opencode pair && exec bash -i'
    end

    function dsh-here
        if test (count $argv) -eq 0
            set argv dsh web --patch /workspace.patch.yml --no-open
        end
        mkdir -p .dsh-data/dsh-home
        __sandbox_launch \
            --bind     .dsh-data/dsh-home $HOME/.dsh \
            --bind-try .dsh-data/ssh      $HOME/.ssh \
            --ro-bind  ~/Projects/env/dsh/workspace.patch.yml /workspace.patch.yml \
            --symlink  /w /d/deepseek-harness/default-workspace \
            -- \
            $argv
    end

    set -x http_proxy http://127.0.0.1:1080
    set -x https_proxy http://127.0.0.1:1080

    . /usr/share/modules/init/fish
    . /usr/share/modules/init/fish_completion
    ml use "$HOME/.local/share/modulefiles"
end
