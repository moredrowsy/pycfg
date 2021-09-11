"""
Run the control flow graph progarm
"""
from argparse import ArgumentParser
from os import walk, path, makedirs
from cfg import ControlFlowGraph


class Run():
    """
    Run Control Flow Graph
    """

    def start(self,):
        """Start"""
        # Get arguments for input and output directory
        args_for_parser = {
            "--inDir": "Input directory",
            "-id": "Input directory",
            "--outDir": "Output directory",
            "-od": "Output directory"
        }
        parser = ArgumentParser()
        for k, v in args_for_parser.items():
            parser.add_argument(k, help=v)
        args = parser.parse_args()

        inDir, outDir = "./input", "./output"

        inDir = args.id if args.id else inDir
        inDir = args.inDir if args.inDir else inDir
        outDir = args.od if args.od else outDir
        outDir = args.outDir if args.outDir else outDir

        filenames = next(walk(inDir), (None, None, []))[2]

        for filename in filenames:
            try:
                cfg = ControlFlowGraph()

                file_path = f"{inDir}/{filename}"
                with open(file_path, "r") as file:
                    for line in file:
                        cfg.add_string(line)

                cfg.parse()

                # Create output file
                text_output_filename = self.get_output_filename(
                    filename, "_output.txt")
                text_output_path = f"{outDir}/{text_output_filename}"
                makedirs(path.dirname(text_output_path), exist_ok=True)
                fout = open(text_output_path, "w+")

                try:
                    print(filename+"\n"+"="*len(filename)+"\n")

                    # Print cfg info
                    output = cfg.print_nodes()

                    print("\n")

                    fout.write(output)
                    fout.write("\n")

                    output = cfg.print_edges()

                    fout.write(output)
                    fout.write("\n")
                    fout.flush()

                    print("\n\n")

                    image_output_filename = self.get_output_filename(
                        filename, ".png")
                    image_output_path = f"{outDir}/{image_output_filename}"
                    # Draw graph
                    cfg.draw_graph(title=filename, filename=image_output_path)
                finally:
                    fout.close()

            except FileNotFoundError as file_error:
                print(f"Error opening {filename}: {file_error}")

    def get_output_filename(self, filename, suffix="output"):
        """Produce an output filename"""
        if not filename:
            return filename

        if "." not in filename:
            return f"{filename}{suffix}"

        extPos = filename.rindex(".")
        return f"{filename[:extPos]}{suffix}"


if __name__ == "__main__":
    Run().start()
