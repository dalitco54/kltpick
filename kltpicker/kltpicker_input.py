from pathlib import Path
from sys import exit
import progressbar
import time 
import argparse
import os

def parse_args(has_cupy):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', help='Input directory.')
    parser.add_argument('--output_dir', help='Output directory.')
    parser.add_argument('-s', '--particle_size', help='Expected size of particles in pixels.', default=300, type=int)
    parser.add_argument('--num_of_particles',
                        help='Number of particles to pick per micrograph. If set to -1 will pick all particles.',
                        default=-1, type=int)
    parser.add_argument('--num_of_noise_images', help='Number of noise images to pick per micrograph.',
                        default=0, type=int)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose.', default=False)
    if has_cupy:
        parser.add_argument('--no_gpu', action='store_true', default=False)
        args = parser.parse_args()
    else:
        args = parser.parse_args()
        args.no_gpu = 1
    return args

def get_args(has_cupy):
    while True:
        input_dir = Path(input('Enter full path of micrographs MRC files:\n'))
        num_files = len(list(input_dir.glob("*.mrc")))
        if num_files > 0:
            print("Found %i MRC files." % len(list(input_dir.glob("*.mrc"))))
            break
        elif not input_dir.is_dir():
            print("%s is not a directory." % input_dir)
        else:
            print("Could not find any files in %s." % input_dir)

    while True:
        output_dir = Path(input('Enter full path of output directory:\n'))
        if output_dir.is_file():
            print("There is already a file with the name you specified. Please specify a directory.")
        elif output_dir.parent.exists() and not output_dir.exists():
            create_dir = input('Output directory does not exist. Create? (Y/N):')
            if create_dir.strip().lower()[0] == 'y':
                Path.mkdir(output_dir)
                break
            else:
                print("OK, exiting...")
                exit(0)
        elif not output_dir.parent.exists():
            print('Parent directory %s does not exist. Please specify an existing directory.' % output_dir.parent)
        else:
            break

    while True:
        particle_size = input('Enter the particle size in pixels:\n')
        try:
            particle_size = int(particle_size)
            if particle_size < 1:
                print("Particle size must be a positive integer.")
            else:
                break
        except ValueError:
            print("Particle size must be a positive integer.")

    num_particles_to_pick = 0
    while num_particles_to_pick == 0:
        pick_all = input('Pick all particles? (Y/N):\n')
        if pick_all.strip().lower()[0] == 'y':
            num_particles_to_pick = -1
        elif pick_all.strip().lower()[0] == 'n':
            while True:
                num_particles_to_pick = input('How many particles to pick:\n')
                try:
                    num_particles_to_pick = int(num_particles_to_pick)
                    if num_particles_to_pick < 1:
                        print("Number of particles to pick must be a positive integer.")
                    else:
                        break
                except ValueError:
                    print("Number of particles to pick must be a positive integer.")
        else:
            print("Please choose Y/N.")

    num_noise_to_pick = -1
    while num_noise_to_pick == -1:
        pick_noise = input('Pick noise images? (Y/N):\n')
        if pick_noise.strip().lower()[0] == 'n':
            num_noise_to_pick = 0
        elif pick_noise.strip().lower()[0] == 'y':
            while True:
                num_noise_to_pick = input('How many noise images to pick:\n')
                try:
                    num_noise_to_pick = int(num_noise_to_pick)
                    if num_noise_to_pick < 1:
                        print("Number of noise images to pick must be a positive integer.")
                    else:
                        break
                except ValueError:
                    print("Number of particles to pick must be a positive integer.")
        else:
            print("Please choose Y/N.")
    
    if has_cupy:
        no_gpu = 0
        while no_gpu == 0:
            no_gpu_in = input('Use GPU? (Y/N):\n')
            if no_gpu_in.strip().lower()[0] == 'n':
                no_gpu = 1
            elif no_gpu_in.strip().lower()[0] == 'y':
                no_gpu == 0
                break
            else:
                print("Please choose Y/N.")
    else:
        no_gpu = 1
    return input_dir, output_dir, particle_size, num_particles_to_pick, num_noise_to_pick, no_gpu

def progress_bar(output_dir, num_mrcs):
    """
    Progress bar function that reports the progress of the program, by 
    periodically checking how many output files have been written. Shows both
    percentage completed and time elapsed.
    """
    start_time = time.time()
    finished = [f for f in output_dir.glob("*.star") if os.path.getmtime(str(f)) > start_time]
    num_finished = len(finished)
    bar = progressbar.ProgressBar(maxval=num_mrcs, widgets=["[", progressbar.Timer(), "] ", progressbar.Bar('#', '|', '|'), ' (', progressbar.Percentage(), ')'])
    bar.start()
    while num_finished < num_mrcs:
        num_finished = len([f for f in output_dir.glob("*.star") if os.path.getmtime(str(f)) > start_time])
        bar.update(num_finished)
        time.sleep(1)
    bar.finish()
    print("Finished successfully!")
    
def write_summary(output_dir, summary):
    print("\nWriting picking summary at the output path.")
    summary_text = "\n".join(["\t".join([str(cell) for cell in row]) for row in summary])
    num_files = len(summary)
    num_particles = sum([row[1] for row in summary])
    num_noise = sum([row[2] for row in summary])   
    with (output_dir / "pickingSummary.txt").open("w") as summary_file:
        summary_file.write("Picking Summary\n")
        summary_file.write("Picked %d particles and %d noise images out of %d micrographs.\n\n" %(num_particles, num_noise, num_files))
        summary_file.write("Picking per micrograph:\nMicrographs name #1\nNumber of picked particles #2\nNumber of picked noise images #3\n--------------------------------\n")   
        summary_file.write(summary_text)
