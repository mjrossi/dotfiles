task :default => "install"

namespace "configs" do
  IGNORE = %w(Rakefile README.md)
  SPECIAL_CONFIG = {}

  desc "symlink files into home directory"
  task :install do
    working_dir = File.dirname(__FILE__)
    for_each_dotfile(working_dir) do |file, dotfile_path|
      puts file
      puts dotfile_path
      # convert_to_backup(dotfile_path)
      
      #FileUtils.ln_s(file, dotfile_path)
    end
  end

  desc "remove symlinks, add old files"
  task :uninstall do
    working_dir = File.dirname(__FILE__)
    for_each_dotfile(working_dir) do |_, dotfile_path|
      puts dotfile_path
      # FileUtils.rm_rf(dotfile_path) if File.symlink?(dotfile_path) || File.exist?(dotfile_path)

      # restore_backup(dotfile_path)
    end
  end

  def for_each_dotfile(dir, &block)
    my_dotfiles = Dir.glob(File.join(dir,"*"))
    my_dotfiles.each do |file|
      filename = File.basename(file)

      next if IGNORE.include?(filename)

      config = SPECIAL_CONFIG[filename] || { dest: "~", symlink: ".#{filename}" }
      dest = File.expand_path(config[:dest])

      FileUtils.mdkdir_p(dest) unless File.directory?(dest)

      dotfile_path = File.join(dest, config[:symlink])

      yield file, dotfile_path
    end
  end

  def convert_to_backup(file)
    File.rename(file, "#{file}.bak") if File.exist?(file)
  end

  def restore_backup(file)
    backup_file = "#{file}.bak"
    File.rename(backup_file, file) if File.exist?(backup_file)
  end
end
